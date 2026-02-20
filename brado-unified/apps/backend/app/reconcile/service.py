from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from typing import Any
from urllib.parse import parse_qs, urlparse

from sqlalchemy import func, or_, select

from ..db.sql.models import IngestionBatch, JobState, RawPayload, ReconcileReport
from ..graph.neo4j import Neo4jWriter
from ..ingest.camara.client import CamaraClient
from ..ingest.camara.endpoints import DEPUTADOS_ENDPOINT, PROPOSICOES_ENDPOINT, VOTACOES_ENDPOINT


@dataclass
class ReconcileResult:
    status: str
    report: dict[str, Any]


class ReconcileService:
    def __init__(self, session):
        self.session = session
        self.client = CamaraClient()
        self.graph = Neo4jWriter()

    def close(self) -> None:
        self.client.close()
        self.graph.close()

    def _scalar_graph(self, query: str, **params: Any) -> int:
        with self.graph.client.driver.session() as neo_session:
            row = neo_session.run(query, **params).single()
            if row is None:
                return 0
            try:
                return int(row["c"])
            except Exception:
                return 0

    @staticmethod
    def _estimate_api_total(body: dict[str, Any], itens_per_page: int = 1) -> int:
        dados = body.get("dados", []) if isinstance(body, dict) else []
        links = body.get("links", []) if isinstance(body, dict) else []
        last_link = next((lnk for lnk in links if lnk.get("rel") == "last"), None)
        if not last_link:
            return len(dados)

        href = last_link.get("href", "")
        qs = parse_qs(urlparse(href).query)
        pagina = qs.get("pagina", [None])[0]
        try:
            return int(pagina) * itens_per_page
        except Exception:
            return len(dados)

    def _issue(
        self,
        *,
        issue_type: str,
        check_name: str,
        counts_expected: int | None,
        counts_actual: int | None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "issue_type": issue_type,
            "check_name": check_name,
            "counts_expected": counts_expected,
            "counts_actual": counts_actual,
            "context": context or {},
        }

    def _expenses_expected_from_raw(self, year: int) -> int:
        rows = self.session.execute(select(RawPayload).where(RawPayload.endpoint.like("/deputados/%/despesas"))).scalars().all()
        total = 0
        for row in rows:
            params = row.params_json or {}
            body = row.body_json if isinstance(row.body_json, dict) else {}
            if int(params.get("ano", -1)) != year:
                continue
            if int(row.http_status or 0) != 200:
                continue
            dados = body.get("dados", []) if isinstance(body.get("dados", []), list) else []
            total += len(dados)
        return total

    def _coverage_checks(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        checks: list[dict[str, Any]] = []
        issues: list[dict[str, Any]] = []

        api_dep_count = 0
        for status, body, _ in self.client.paginated(DEPUTADOS_ENDPOINT, {"itens": 100}):
            if status != 200:
                continue
            api_dep_count += len(body.get("dados", []))

        graph_dep_count = self._scalar_graph("MATCH (n:Person) RETURN count(n) as c")
        dep_ok = graph_dep_count == api_dep_count and api_dep_count > 0
        dep_check = {
            "name": "coverage_deputados_current",
            "domain": "deputados",
            "counts_expected": api_dep_count,
            "counts_actual": graph_dep_count,
            "ok": dep_ok,
            "gate": True,
        }
        checks.append(dep_check)
        if not dep_ok:
            issues.append(
                self._issue(
                    issue_type="coverage_deputados",
                    check_name=dep_check["name"],
                    counts_expected=api_dep_count,
                    counts_actual=graph_dep_count,
                )
            )

        expense_people_count = self._scalar_graph(
            "MATCH (p:Person)-[:HAS_EXPENSE]->(e:Expense) WHERE toInteger(coalesce(e.year, 0)) >= 2018 RETURN count(DISTINCT p) as c"
        )
        expense_people_gate = self._expense_people_coverage_gate_enabled()
        expense_people_ok = expense_people_count >= api_dep_count and api_dep_count > 0
        dep_with_expense_check = {
            "name": "coverage_deputados_with_expenses_since_2018",
            "domain": "expenses",
            "counts_expected": api_dep_count,
            "counts_actual": expense_people_count,
            "ok": expense_people_ok,
            "gate": expense_people_gate,
            "justification": "requires full, non-filtered expenses backfill",
        }
        checks.append(dep_with_expense_check)
        if not expense_people_ok and expense_people_gate:
            issues.append(
                self._issue(
                    issue_type="coverage_deputados_with_expenses",
                    check_name=dep_with_expense_check["name"],
                    counts_expected=api_dep_count,
                    counts_actual=expense_people_count,
                )
            )

        current_year = datetime.now(timezone.utc).year
        for year in range(2018, current_year + 1):
            bills_gate = self._year_fully_covered_by_batches("camara:bills:", year)
            votes_gate = self._year_fully_covered_by_batches("camara:votes:", year)
            expenses_gate = self._year_fully_covered_by_batches("camara:expenses:", year)

            try:
                _, bills = self.client.get(PROPOSICOES_ENDPOINT, {"ano": year, "itens": 1})
                api_bill_count = self._estimate_api_total(bills, itens_per_page=1)
            except Exception:
                api_bill_count = 0
            graph_bill_count = self._scalar_graph(
                "MATCH (b:Bill) WHERE toInteger(coalesce(b.ano, 0)) = $year RETURN count(b) as c",
                year=year,
            )
            bills_ok = graph_bill_count >= api_bill_count and api_bill_count >= 0
            bill_check = {
                "name": "coverage_bills_year",
                "domain": "bills",
                "year": year,
                "counts_expected": api_bill_count,
                "counts_actual": graph_bill_count,
                "ok": bills_ok,
                "gate": bills_gate,
            }
            checks.append(bill_check)
            if not bills_ok and bills_gate:
                issues.append(
                    self._issue(
                        issue_type="coverage_bills_year",
                        check_name=bill_check["name"],
                        counts_expected=api_bill_count,
                        counts_actual=graph_bill_count,
                        context={"year": year},
                    )
                )

            try:
                _, votes = self.client.get(VOTACOES_ENDPOINT, {"ano": year, "itens": 1})
                api_vote_count = self._estimate_api_total(votes, itens_per_page=1)
            except Exception:
                api_vote_count = 0
            graph_vote_count = self._scalar_graph(
                "MATCH (v:VoteEvent) WHERE v.dataHoraRegistro STARTS WITH $prefix RETURN count(v) as c",
                prefix=f"{year}-",
            )
            votes_ok = graph_vote_count >= api_vote_count and api_vote_count >= 0
            vote_check = {
                "name": "coverage_votes_year",
                "domain": "votes",
                "year": year,
                "counts_expected": api_vote_count,
                "counts_actual": graph_vote_count,
                "ok": votes_ok,
                "gate": votes_gate,
            }
            checks.append(vote_check)
            if not votes_ok and votes_gate:
                issues.append(
                    self._issue(
                        issue_type="coverage_votes_year",
                        check_name=vote_check["name"],
                        counts_expected=api_vote_count,
                        counts_actual=graph_vote_count,
                        context={"year": year},
                    )
                )

            expected_expenses = self._expenses_expected_from_raw(year)
            graph_expenses_year = self._scalar_graph(
                "MATCH (e:Expense) WHERE toInteger(coalesce(e.year, 0)) = $year RETURN count(e) as c",
                year=year,
            )
            expenses_ok = graph_expenses_year >= expected_expenses
            expense_check = {
                "name": "coverage_expenses_year",
                "domain": "expenses",
                "year": year,
                "counts_expected": expected_expenses,
                "counts_actual": graph_expenses_year,
                "ok": expenses_ok,
                "gate": expenses_gate,
                "justification": "expected derived from raw_payloads for year",
            }
            checks.append(expense_check)
            if not expenses_ok and expenses_gate:
                issues.append(
                    self._issue(
                        issue_type="coverage_expenses_year",
                        check_name=expense_check["name"],
                        counts_expected=expected_expenses,
                        counts_actual=graph_expenses_year,
                        context={"year": year},
                    )
                )

        return checks, issues

    def _expense_people_coverage_gate_enabled(self) -> bool:
        state = self.session.get(JobState, "ingest_expenses_since")
        if not state or state.status != "success":
            return False
        cursor = state.cursor_json or {}
        selected = cursor.get("deputado_ids", [])
        return not bool(selected)

    def _year_fully_covered_by_batches(self, batch_prefix: str, year: int) -> bool:
        batches = (
            self.session.execute(
                select(IngestionBatch).where(
                    IngestionBatch.batch_type.like(f"{batch_prefix}%"),
                    IngestionBatch.status == "success",
                )
            )
            .scalars()
            .all()
        )
        if not batches:
            return False
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        for batch in batches:
            if not batch.range_start or not batch.range_end:
                continue
            if batch.range_start <= year_start and batch.range_end >= year_end:
                return True
        return False

    def _integrity_checks(self) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []

        orphan_vote_actions_no_event = self._scalar_graph(
            "MATCH (va:VoteAction) WHERE NOT (va)-[:IN_EVENT]->(:VoteEvent) RETURN count(va) as c"
        )
        checks.append(
            {
                "name": "integrity_vote_action_has_event",
                "issue_type": "referential_integrity",
                "counts_expected": 0,
                "counts_actual": orphan_vote_actions_no_event,
                "orphans": orphan_vote_actions_no_event,
                "ok": orphan_vote_actions_no_event == 0,
                "gate": True,
            }
        )

        orphan_vote_actions_no_person = self._scalar_graph(
            "MATCH (va:VoteAction) WHERE NOT (:Person)-[:CAST]->(va) RETURN count(va) as c"
        )
        checks.append(
            {
                "name": "integrity_vote_action_has_person",
                "issue_type": "referential_integrity",
                "counts_expected": 0,
                "counts_actual": orphan_vote_actions_no_person,
                "orphans": orphan_vote_actions_no_person,
                "ok": orphan_vote_actions_no_person == 0,
                "gate": True,
            }
        )

        orphan_expenses = self._scalar_graph("MATCH (e:Expense) WHERE NOT (:Person)-[:HAS_EXPENSE]->(e) RETURN count(e) as c")
        checks.append(
            {
                "name": "integrity_expense_has_person",
                "issue_type": "referential_integrity",
                "counts_expected": 0,
                "counts_actual": orphan_expenses,
                "orphans": orphan_expenses,
                "ok": orphan_expenses == 0,
                "gate": True,
            }
        )

        dangling_vote_events_bill = self._scalar_graph(
            "MATCH (v:VoteEvent) WHERE v.billId IS NOT NULL AND NOT (v)-[:ON_BILL]->(:Bill) RETURN count(v) as c"
        )
        checks.append(
            {
                "name": "integrity_vote_event_bill_link",
                "issue_type": "referential_integrity",
                "counts_expected": 0,
                "counts_actual": dangling_vote_events_bill,
                "orphans": dangling_vote_events_bill,
                "ok": dangling_vote_events_bill == 0,
                "gate": True,
            }
        )

        return checks

    def _uniqueness_checks(self) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        for label in ["Person", "Bill", "VoteEvent", "VoteAction", "Expense", "Organization", "Party", "State"]:
            dup = self._scalar_graph(
                f"MATCH (n:{label}) WITH n.id as id, count(*) as c WHERE c > 1 RETURN count(*) as c"
            )
            checks.append(
                {
                    "name": f"uniqueness_{label.lower()}",
                    "issue_type": "uniqueness",
                    "counts_expected": 0,
                    "counts_actual": dup,
                    "ok": dup == 0,
                    "gate": True,
                }
            )
        return checks

    def _temporal_checks(self) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        invalid_batches = 0
        batches = self.session.execute(select(IngestionBatch)).scalars().all()
        for batch in batches:
            if not batch.range_start or not batch.range_end:
                continue
            out_of_range = self.session.scalar(
                select(func.count(RawPayload.id)).where(
                    RawPayload.batch_id == batch.id,
                    or_(
                        func.date(RawPayload.fetched_at) < batch.range_start,
                        func.date(RawPayload.fetched_at) > batch.range_end,
                    ),
                )
            ) or 0
            if out_of_range > 0:
                invalid_batches += 1
        checks.append(
            {
                "name": "temporal_batch_fetched_at_consistent",
                "issue_type": "temporal_consistency",
                "counts_expected": 0,
                "counts_actual": invalid_batches,
                "ok": invalid_batches == 0,
                "gate": True,
            }
        )
        return checks

    def _nominal_vote_availability_check(self) -> dict[str, Any]:
        rows = self.session.execute(select(RawPayload).where(RawPayload.endpoint.like("/votacoes/%/votos"))).scalars().all()
        unavailable = 0
        undocumented_non_200 = 0
        for row in rows:
            body = row.body_json if isinstance(row.body_json, dict) else {}
            metadata = body.get("metadata", {}) if isinstance(body.get("metadata", {}), dict) else {}
            error_type = metadata.get("error_type")
            if int(row.http_status or 0) != 200 and not error_type:
                undocumented_non_200 += 1
            if error_type == "nominal_votes_not_available":
                unavailable += 1

        return {
            "name": "coverage_nominal_votes_unavailable_documented",
            "issue_type": "nominal_votes",
            "counts_expected": 0,
            "counts_actual": undocumented_non_200,
            "unavailable_count": unavailable,
            "ok": undocumented_non_200 == 0,
            "gate": True,
        }

    def _documented_expense_gap_check(self) -> dict[str, Any]:
        latest = (
            self.session.execute(
                select(IngestionBatch)
                .where(IngestionBatch.batch_type.like("camara:expenses:%"), IngestionBatch.status == "success")
                .order_by(IngestionBatch.started_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        if not latest or not latest.notes:
            return {
                "name": "coverage_expenses_documented_gaps",
                "issue_type": "coverage_expenses_documented_gaps",
                "counts_expected": 0,
                "counts_actual": 0,
                "ok": True,
                "gate": True,
            }
        try:
            metadata = json.loads(latest.notes)
        except Exception:
            metadata = {}
        gaps = metadata.get("coverage_gaps", []) if isinstance(metadata, dict) else []
        gap_count = len(gaps) if isinstance(gaps, list) else 0
        return {
            "name": "coverage_expenses_documented_gaps",
            "issue_type": "coverage_expenses_documented_gaps",
            "counts_expected": 0,
            "counts_actual": gap_count,
            "ok": gap_count == 0,
            "gate": True,
        }

    def _extract_raw_dados(self, raw_body: Any) -> Any:
        if isinstance(raw_body, dict):
            return raw_body.get("dados", raw_body)
        return raw_body

    def _audit_samples(self, label: str, limit: int = 50) -> dict[str, Any]:
        key_map = {
            "Bill": ["sourceId", "ano", "numero"],
            "VoteEvent": ["sourceId", "dataHoraRegistro"],
            "Expense": ["sourceId", "year", "month"],
        }
        graph_rows: list[dict[str, Any]] = []
        with self.graph.client.driver.session() as neo_session:
            rows = neo_session.run(
                f"MATCH (n:{label}) RETURN n.id as id, n.sourceId as sourceId, n.rawRefs as rawRefs, n.rawRef as rawRef, n.ano as ano, n.numero as numero, n.dataHoraRegistro as dataHoraRegistro, n.year as year, n.month as month LIMIT $limit",
                limit=limit,
            )
            graph_rows = [dict(row) for row in rows]

        mismatches = 0
        checked = 0
        keys = key_map.get(label, ["sourceId"])
        for row in graph_rows:
            raw_ids = row.get("rawRefs") or ([] if row.get("rawRef") is None else [row.get("rawRef")])
            if not raw_ids:
                continue
            raw = self.session.get(RawPayload, raw_ids[0])
            if not raw:
                mismatches += 1
                checked += 1
                continue
            dados = self._extract_raw_dados(raw.body_json)
            if isinstance(dados, list) and dados:
                dados = dados[0]
            if not isinstance(dados, dict):
                mismatches += 1
                checked += 1
                continue

            local_mismatch = False
            for key in keys:
                if key == "sourceId" and str(row.get("sourceId")) != str(dados.get("id")):
                    local_mismatch = True
                elif key == "ano" and row.get("ano") is not None and int(row.get("ano")) != int(dados.get("ano", -1)):
                    local_mismatch = True
                elif key == "numero" and row.get("numero") is not None and str(row.get("numero")) != str(dados.get("numero")):
                    local_mismatch = True
                elif key == "dataHoraRegistro" and row.get("dataHoraRegistro") and str(dados.get("dataHoraRegistro", "")) != str(row.get("dataHoraRegistro")):
                    local_mismatch = True
                elif key == "year" and row.get("year") is not None and int(row.get("year")) != int(dados.get("ano", -1)):
                    local_mismatch = True
                elif key == "month" and row.get("month") is not None and int(row.get("month")) != int(dados.get("mes", -1)):
                    local_mismatch = True
            mismatches += 1 if local_mismatch else 0
            checked += 1

        ok = checked == 0 or mismatches == 0
        return {
            "name": f"audit_sample_raw_vs_graph_{label.lower()}",
            "issue_type": "audit",
            "counts_expected": 0,
            "counts_actual": mismatches,
            "label": label,
            "checked": checked,
            "mismatches": mismatches,
            "ok": ok,
            "gate": True,
        }

    def reconcile_all(self) -> ReconcileResult:
        checks: list[dict[str, Any]] = []
        issues: list[dict[str, Any]] = []

        coverage_checks, coverage_issues = self._coverage_checks()
        checks.extend(coverage_checks)
        issues.extend(coverage_issues)

        checks.extend(self._integrity_checks())
        checks.extend(self._uniqueness_checks())
        checks.extend(self._temporal_checks())
        checks.append(self._nominal_vote_availability_check())
        checks.append(self._documented_expense_gap_check())

        raw_count = self.session.scalar(select(func.count(RawPayload.id))) or 0
        checks.append(
            {
                "name": "raw_payload_exists",
                "issue_type": "raw",
                "counts_expected": 1,
                "counts_actual": int(raw_count),
                "ok": raw_count > 0,
                "gate": True,
            }
        )

        checks.extend([self._audit_samples("Bill", 50), self._audit_samples("VoteEvent", 50), self._audit_samples("Expense", 50)])

        for check in checks:
            if check.get("ok", False):
                continue
            if not check.get("gate", True):
                continue
            issues.append(
                self._issue(
                    issue_type=check.get("issue_type", "reconcile_check_failed"),
                    check_name=check.get("name", "unknown"),
                    counts_expected=check.get("counts_expected"),
                    counts_actual=check.get("counts_actual"),
                    context={k: v for k, v in check.items() if k not in {"name", "issue_type", "counts_expected", "counts_actual", "ok", "gate"}},
                )
            )

        status = "success" if not issues else "failed"

        report = {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "checks": checks,
            "issues": issues,
            "coverage_gap": issues,
        }

        report_row = ReconcileReport(status=status, report_json=report)
        self.session.add(report_row)
        self.session.flush()

        return ReconcileResult(status=status, report={"id": report_row.id, **report})
