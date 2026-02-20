from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import csv
import io
import json
import random
from typing import Any

from ..core.config import get_settings
from ..db.raw_store import RawStore
from ..db.sql.models import JobState
from ..graph.neo4j import Neo4jWriter
from ..ingest.camara.client import CamaraClient
from ..ingest.camara.endpoints import (
    DEPUTADOS_ENDPOINT,
    PROPOSICOES_ENDPOINT,
    VOTACOES_ENDPOINT,
    deputado_details_endpoint,
    despesas_endpoint,
    proposicao_details_endpoint,
    votacao_details_endpoint,
    votacao_votos_endpoint,
)
from ..normalize.mappers import (
    normalize_bill,
    normalize_expense,
    normalize_person,
    normalize_vote_action,
    normalize_vote_event,
)


@dataclass
class JobContext:
    session: Any
    raw_store: RawStore
    client: CamaraClient
    graph: Neo4jWriter


class IngestJobs:
    def __init__(self, session):
        self.session = session
        self.raw_store = RawStore(session)
        self.client = CamaraClient()
        self.graph = Neo4jWriter()
        self._max_workers = max(1, get_settings().camara_max_concurrency)

    def close(self) -> None:
        self.client.close()
        self.graph.close()

    def _get_job_state(self, job_name: str) -> JobState:
        state = self.session.get(JobState, job_name)
        if state:
            return state
        state = JobState(job_name=job_name, cursor_json={}, status="idle")
        self.session.add(state)
        self.session.flush()
        return state

    def _set_job_state(self, job_name: str, status: str, cursor: dict[str, Any] | None = None) -> None:
        state = self._get_job_state(job_name)
        state.status = status
        state.cursor_json = cursor or {}
        self.session.add(state)
        self.session.flush()

    def _resume_cursor(self, job_name: str) -> dict[str, Any]:
        state = self._get_job_state(job_name)
        return state.cursor_json or {}

    def ingest_deputados_current(self, max_pages: int | None = None) -> dict[str, Any]:
        job_name = "ingest_deputados_current"
        resume = self._resume_cursor(job_name)
        start_page = int(resume.get("page", 1))
        self._set_job_state(job_name, "running", {"page": start_page})
        batch = self.raw_store.start_batch("camara", "camara:deputados:current")

        total = 0
        try:
            self.graph.ensure_constraints()
            for status, body, params in self.client.paginated(DEPUTADOS_ENDPOINT, {"itens": 100, "pagina": start_page}, max_pages=max_pages):
                self.raw_store.add_payload(
                    batch=batch,
                    endpoint=DEPUTADOS_ENDPOINT,
                    params=params,
                    primary_key=None,
                    http_status=status,
                    body_json=body,
                )
                for dep in body.get("dados", []):
                    dep_id = dep.get("id")
                    if not dep_id:
                        continue
                    detail_endpoint = deputado_details_endpoint(dep_id)
                    d_status, d_body = self.client.get(detail_endpoint)
                    raw = self.raw_store.add_payload(
                        batch=batch,
                        endpoint=detail_endpoint,
                        params={},
                        primary_key=str(dep_id),
                        http_status=d_status,
                        body_json=d_body,
                    )
                    node = normalize_person(d_body.get("dados", dep))
                    self.graph.upsert_person(node, raw.id)
                    total += 1
                self._set_job_state(job_name, "running", {"page": params.get("pagina", start_page), "processed": total})

            self.raw_store.finish_batch(batch, metadata={"item_count": total})
            self._set_job_state(job_name, "success", {"processed": total})
            return {"job": job_name, "status": "success", "processed": total, "batch_id": batch.id}
        except Exception as exc:
            self.raw_store.fail_batch(batch, str(exc))
            self._set_job_state(job_name, "failed", {"error": str(exc)})
            raise

    def ingest_bills_since(self, from_date: date, to_date: date | None = None, max_pages: int | None = None) -> dict[str, Any]:
        job_name = "ingest_bills_since"
        end_date = to_date or date.today()
        self._set_job_state(job_name, "running", {"from": str(from_date), "to": str(end_date), "window_index": 0})
        batch = self.raw_store.start_batch("camara", f"camara:bills:{from_date.isoformat()}", from_date, end_date)

        processed = 0
        coverage_gaps: list[dict[str, Any]] = []
        try:
            for window_index, (window_start, window_end) in enumerate(self._date_windows(from_date, end_date), start=1):
                try:
                    params = {
                        "dataInicio": window_start.isoformat(),
                        "dataFim": window_end.isoformat(),
                        "ordenarPor": "id",
                        "ordem": "ASC",
                        "itens": 100,
                        "pagina": 1,
                    }
                    for status, body, page_params in self.client.paginated(PROPOSICOES_ENDPOINT, params, max_pages=max_pages):
                        self.raw_store.add_payload(
                            batch=batch,
                            endpoint=PROPOSICOES_ENDPOINT,
                            params=page_params,
                            primary_key=None,
                            http_status=status,
                            body_json=body,
                        )

                        props = [prop for prop in body.get("dados", []) if prop.get("id")]
                        detail_requests = [(proposicao_details_endpoint(prop["id"]), {}) for prop in props]
                        detail_responses = self.client.fetch_many(detail_requests, max_workers=self._max_workers)

                        for prop, (d_status, d_body) in zip(props, detail_responses):
                            prop_id = prop.get("id")
                            detail_endpoint = proposicao_details_endpoint(prop_id)
                            raw = self.raw_store.add_payload(
                                batch=batch,
                                endpoint=detail_endpoint,
                                params={},
                                primary_key=str(prop_id),
                                http_status=d_status,
                                body_json=d_body,
                            )
                            bill = normalize_bill(d_body.get("dados", prop))
                            self.graph.upsert_bill(bill, raw.id)
                            processed += 1

                        self._set_job_state(
                            job_name,
                            "running",
                            {
                                "from": str(from_date),
                                "to": str(end_date),
                                "window_index": window_index,
                                "window_start": str(window_start),
                                "window_end": str(window_end),
                                "page": page_params.get("pagina", 1),
                                "processed": processed,
                            },
                        )
                except Exception as exc:
                    fallback_rows = self._ingest_bills_static_fallback(
                        batch=batch,
                        from_date=window_start,
                        to_date=window_end,
                    )
                    coverage_gaps.append(
                        {
                            "window_start": window_start.isoformat(),
                            "window_end": window_end.isoformat(),
                            "reason": str(exc),
                            "fallback_rows": fallback_rows,
                        }
                    )
                    processed += fallback_rows
                    self._set_job_state(
                        job_name,
                        "running",
                        {
                            "from": str(from_date),
                            "to": str(end_date),
                            "window_index": window_index,
                            "window_start": str(window_start),
                            "window_end": str(window_end),
                            "processed": processed,
                            "fallback": True,
                        },
                    )
                    continue

            self.raw_store.finish_batch(batch, metadata={"processed": processed, "coverage_gaps": coverage_gaps})
            self._set_job_state(job_name, "success", {"processed": processed})
            return {"job": job_name, "status": "success", "processed": processed, "batch_id": batch.id}
        except Exception as exc:
            self.raw_store.fail_batch(batch, str(exc))
            self._set_job_state(job_name, "failed", {"error": str(exc)})
            raise

    def ingest_votes_since(
        self,
        from_date: date,
        to_date: date | None = None,
        deputado_ids: list[int] | None = None,
        max_pages: int | None = None,
    ) -> dict[str, Any]:
        job_name = "ingest_votes_since"
        end_date = to_date or date.today()
        selected_ids = set(deputado_ids or [])
        self._set_job_state(
            job_name,
            "running",
            {"from": str(from_date), "to": str(end_date), "window_index": 0, "deputado_ids": sorted(selected_ids)},
        )
        batch = self.raw_store.start_batch("camara", f"camara:votes:{from_date.isoformat()}", from_date, end_date)

        processed_events = 0
        processed_actions = 0
        coverage_gaps: list[dict[str, Any]] = []
        try:
            for window_index, (window_start, window_end) in enumerate(self._date_windows(from_date, end_date), start=1):
                try:
                    params = {
                        "dataInicio": window_start.isoformat(),
                        "dataFim": window_end.isoformat(),
                        "ordenarPor": "id",
                        "ordem": "ASC",
                        "itens": 100,
                        "pagina": 1,
                    }
                    for status, body, page_params in self.client.paginated(VOTACOES_ENDPOINT, params, max_pages=max_pages):
                        self.raw_store.add_payload(
                            batch=batch,
                            endpoint=VOTACOES_ENDPOINT,
                            params=page_params,
                            primary_key=None,
                            http_status=status,
                            body_json=body,
                        )

                        events = [event for event in body.get("dados", []) if event.get("id")]
                        detail_requests = [(votacao_details_endpoint(event["id"]), {}) for event in events]
                        nominal_requests = [(votacao_votos_endpoint(event["id"]), {}) for event in events]
                        detail_responses = self.client.fetch_many(detail_requests, max_workers=self._max_workers)
                        nominal_responses = self.client.fetch_many(
                            nominal_requests,
                            max_workers=self._max_workers,
                            raise_for_status=False,
                        )

                        for voto_event, (d_status, d_body), (v_status, v_body) in zip(events, detail_responses, nominal_responses):
                            votacao_id = voto_event.get("id")
                            detail_endpoint = votacao_details_endpoint(votacao_id)
                            raw_event = self.raw_store.add_payload(
                                batch=batch,
                                endpoint=detail_endpoint,
                                params={},
                                primary_key=str(votacao_id),
                                http_status=d_status,
                                body_json=d_body,
                            )
                            node = normalize_vote_event(d_body.get("dados", voto_event))
                            self.graph.upsert_vote_event(node, raw_event.id)
                            processed_events += 1

                            votos_endpoint = votacao_votos_endpoint(votacao_id)
                            normalized_v_body = v_body if isinstance(v_body, dict) else {"dados": []}
                            if v_status != 200:
                                metadata = dict(normalized_v_body.get("metadata", {}))
                                metadata["error_type"] = self._nominal_vote_error_type(v_status)
                                metadata["status_code"] = v_status
                                normalized_v_body["metadata"] = metadata
                                normalized_v_body.setdefault("dados", [])
                                self.raw_store.add_payload(
                                    batch=batch,
                                    endpoint=votos_endpoint,
                                    params={},
                                    primary_key=str(votacao_id),
                                    http_status=v_status,
                                    body_json=normalized_v_body,
                                )
                                continue

                            raw_votes = self.raw_store.add_payload(
                                batch=batch,
                                endpoint=votos_endpoint,
                                params={},
                                primary_key=str(votacao_id),
                                http_status=v_status,
                                body_json=normalized_v_body,
                            )
                            for voto in normalized_v_body.get("dados", []):
                                deputado_id = voto.get("deputado_", {}).get("id") or voto.get("idDeputado")
                                if not deputado_id:
                                    continue
                                try:
                                    dep_id_int = int(deputado_id)
                                except Exception:
                                    continue
                                if selected_ids and dep_id_int not in selected_ids:
                                    continue
                                person_node_id = f"camara:person:{deputado_id}"
                                action = normalize_vote_action(voto, node["id"], person_node_id)
                                self.graph.upsert_vote_action(action, raw_votes.id)
                                processed_actions += 1

                        self._set_job_state(
                            job_name,
                            "running",
                            {
                                "from": str(from_date),
                                "to": str(end_date),
                                "window_index": window_index,
                                "window_start": str(window_start),
                                "window_end": str(window_end),
                                "page": page_params.get("pagina", 1),
                                "events": processed_events,
                                "actions": processed_actions,
                                "deputado_ids": sorted(selected_ids),
                            },
                        )
                except Exception as exc:
                    fb_events, fb_actions = self._ingest_votes_static_fallback(
                        batch=batch,
                        from_date=window_start,
                        to_date=window_end,
                        deputado_ids=sorted(selected_ids),
                    )
                    coverage_gaps.append(
                        {
                            "window_start": window_start.isoformat(),
                            "window_end": window_end.isoformat(),
                            "reason": str(exc),
                            "fallback_events": fb_events,
                            "fallback_actions": fb_actions,
                        }
                    )
                    processed_events += fb_events
                    processed_actions += fb_actions
                    self._set_job_state(
                        job_name,
                        "running",
                        {
                            "from": str(from_date),
                            "to": str(end_date),
                            "window_index": window_index,
                            "window_start": str(window_start),
                            "window_end": str(window_end),
                            "events": processed_events,
                            "actions": processed_actions,
                            "deputado_ids": sorted(selected_ids),
                            "fallback": True,
                        },
                    )
                    continue

            self.raw_store.finish_batch(
                batch,
                metadata={"events": processed_events, "actions": processed_actions, "coverage_gaps": coverage_gaps},
            )
            self._set_job_state(job_name, "success", {"events": processed_events, "actions": processed_actions})
            return {
                "job": job_name,
                "status": "success",
                "events": processed_events,
                "actions": processed_actions,
                "batch_id": batch.id,
            }
        except Exception as exc:
            self.raw_store.fail_batch(batch, str(exc))
            self._set_job_state(job_name, "failed", {"error": str(exc)})
            raise

    @staticmethod
    def _date_windows(from_date: date, to_date: date, max_days: int = 90) -> list[tuple[date, date]]:
        windows: list[tuple[date, date]] = []
        cursor = from_date
        while cursor <= to_date:
            window_end = min(cursor + timedelta(days=max_days - 1), to_date)
            windows.append((cursor, window_end))
            cursor = window_end + timedelta(days=1)
        return windows

    def ingest_expenses_since(
        self,
        from_date: date,
        to_date: date | None = None,
        deputado_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        job_name = "ingest_expenses_since"
        resume = self._resume_cursor(job_name)
        end_date = to_date or date.today()
        dep_cursor = int(resume.get("dep_index", 0))
        year_cursor = int(resume.get("year", from_date.year))
        selected_ids = set(deputado_ids or [])
        self._set_job_state(
            job_name,
            "running",
            {
                "from": str(from_date),
                "to": str(end_date),
                "dep_index": dep_cursor,
                "year": year_cursor,
                "deputado_ids": sorted(selected_ids),
            },
        )
        batch = self.raw_store.start_batch("camara", f"camara:expenses:{from_date.isoformat()}", from_date, end_date)

        processed = 0
        coverage_gaps: list[dict[str, Any]] = []
        fallback_rows = 0

        try:
            current_deputado_ids: list[int] = []
            for dep_status, deps_body, dep_params in self.client.paginated(DEPUTADOS_ENDPOINT, {"itens": 100}, max_pages=None):
                self.raw_store.add_payload(
                    batch=batch,
                    endpoint=DEPUTADOS_ENDPOINT,
                    params=dep_params,
                    primary_key=f"expenses_seed:{dep_params.get('pagina', 1)}",
                    http_status=dep_status,
                    body_json=deps_body,
                )
                current_deputado_ids.extend([int(d.get("id")) for d in deps_body.get("dados", []) if d.get("id")])
            if selected_ids:
                current_deputado_ids = [dep_id for dep_id in current_deputado_ids if dep_id in selected_ids]
            current_deputado_ids = sorted(set(current_deputado_ids))
            start_year = from_date.year
            end_year = end_date.year

            for dep_index, dep_id in enumerate(current_deputado_ids):
                if dep_index < dep_cursor:
                    continue
                year_start = year_cursor if dep_index == dep_cursor else start_year
                for year in range(year_start, end_year + 1):
                    endpoint = despesas_endpoint(dep_id)
                    try:
                        for status, body, page_params in self.client.paginated(endpoint, {"ano": year, "itens": 100}, max_pages=None):
                            raw = self.raw_store.add_payload(
                                batch=batch,
                                endpoint=endpoint,
                                params=page_params,
                                primary_key=f"{dep_id}:{year}:{page_params.get('pagina', 1)}",
                                http_status=status,
                                body_json=body,
                            )
                            for expense in body.get("dados", []):
                                node = normalize_expense(expense, dep_id)
                                self.graph.upsert_expense(node, raw.id)
                                processed += 1
                        self._set_job_state(
                            job_name,
                            "running",
                            {
                                "from": str(from_date),
                                "to": str(end_date),
                                "dep_index": dep_index,
                                "year": year,
                                "processed": processed,
                                "deputado_ids": sorted(selected_ids),
                            },
                        )
                    except Exception as exc:
                        coverage_gaps.append({"deputado_id": dep_id, "year": year, "reason": str(exc)})

            if coverage_gaps:
                fallback_rows = self._ingest_expenses_dataset_fallback(
                    batch=batch,
                    from_date=from_date,
                    to_date=end_date,
                    deputado_ids=current_deputado_ids,
                    coverage_gaps=coverage_gaps,
                )

            self.raw_store.finish_batch(
                batch,
                metadata={"processed": processed, "fallback_rows": fallback_rows, "coverage_gaps": coverage_gaps},
            )
            self._set_job_state(
                job_name,
                "success",
                {
                    "processed": processed,
                    "fallback_rows": fallback_rows,
                    "coverage_gaps": len(coverage_gaps),
                    "deputado_ids": sorted(selected_ids),
                    "from": str(from_date),
                    "to": str(end_date),
                },
            )
            return {
                "job": job_name,
                "status": "success",
                "processed": processed,
                "fallback_rows": fallback_rows,
                "coverage_gaps": coverage_gaps,
                "batch_id": batch.id,
            }
        except Exception as exc:
            self.raw_store.fail_batch(batch, str(exc))
            self._set_job_state(job_name, "failed", {"error": str(exc)})
            raise

    def smoke_real(self, sample_size: int = 5) -> dict[str, Any]:
        today = date.today()
        from_date = today - timedelta(days=30)
        deputado_ids: list[int] = []
        for status, body, _params in self.client.paginated(DEPUTADOS_ENDPOINT, {"itens": 100}, max_pages=None):
            if status != 200:
                raise RuntimeError("Could not fetch deputados for smoke")
            deputado_ids.extend([int(item["id"]) for item in body.get("dados", []) if item.get("id")])
        deputado_ids = sorted(set(deputado_ids))
        if not deputado_ids:
            raise RuntimeError("No deputados available for smoke")
        selected = random.sample(deputado_ids, k=min(sample_size, len(deputado_ids)))
        return {
            "window": {"from": from_date.isoformat(), "to": today.isoformat()},
            "selected_deputados": selected,
            "deputados": self.ingest_deputados_current(),
            "votes_recent": self.ingest_votes_since(from_date, to_date=today, deputado_ids=selected, max_pages=3),
            "expenses_recent": self.ingest_expenses_since(from_date, to_date=today, deputado_ids=selected),
        }

    @staticmethod
    def _nominal_vote_error_type(status_code: int) -> str:
        if status_code == 404:
            return "nominal_votes_not_available"
        if status_code >= 500:
            return "upstream_error"
        return "nominal_votes_http_error"

    @staticmethod
    def _coerce_date(value: Any) -> date | None:
        if value in (None, ""):
            return None
        raw = str(value).strip()
        if not raw:
            return None
        if "T" in raw:
            raw = raw.split("T", 1)[0]
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None

    @staticmethod
    def _iter_static_records(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            if isinstance(payload.get("dados"), list):
                return [row for row in payload["dados"] if isinstance(row, dict)]
            if isinstance(payload.get("data"), list):
                return [row for row in payload["data"] if isinstance(row, dict)]
        return []

    def _ingest_bills_static_fallback(self, *, batch: Any, from_date: date, to_date: date) -> int:
        template = get_settings().camara_proposicoes_static_url_template.strip()
        if not template:
            return 0

        processed = 0
        for year in range(from_date.year, to_date.year + 1):
            url = template.format(year=year)
            status, raw_text = self.client.get_text(url, raise_for_status=False)
            raw = self.raw_store.add_payload(
                batch=batch,
                endpoint=f"/datasets/proposicoes/{year}",
                params={"year": year, "url": url},
                primary_key=str(year),
                http_status=status,
                body_json={"metadata": {"url": url, "year": year, "status_code": status}},
                source="camara_dataset",
            )
            if status != 200 or not raw_text.strip():
                continue
            try:
                payload = json.loads(raw_text)
            except Exception:
                continue
            for row in self._iter_static_records(payload):
                row_date = self._coerce_date(row.get("dataApresentacao") or row.get("data"))
                if row_date and (row_date < from_date or row_date > to_date):
                    continue
                prop_id = row.get("id") or row.get("idProposicao")
                if not prop_id:
                    continue
                try:
                    bill = normalize_bill(row if isinstance(row, dict) else {"id": prop_id})
                    self.graph.upsert_bill(bill, raw.id)
                    processed += 1
                except Exception:
                    continue
        return processed

    def _ingest_votes_static_fallback(
        self,
        *,
        batch: Any,
        from_date: date,
        to_date: date,
        deputado_ids: list[int],
    ) -> tuple[int, int]:
        settings = get_settings()
        votes_template = settings.camara_votacoes_static_url_template.strip()
        votes_nominal_template = settings.camara_votacoes_votos_static_url_template.strip()
        if not votes_template:
            return 0, 0

        selected_ids = set(deputado_ids)
        events_count = 0
        actions_count = 0

        for year in range(from_date.year, to_date.year + 1):
            event_node_by_votacao: dict[str, str] = {}

            votes_url = votes_template.format(year=year)
            votes_status, votes_text = self.client.get_text(votes_url, raise_for_status=False)
            raw_votes_year = self.raw_store.add_payload(
                batch=batch,
                endpoint=f"/datasets/votacoes/{year}",
                params={"year": year, "url": votes_url},
                primary_key=str(year),
                http_status=votes_status,
                body_json={"metadata": {"url": votes_url, "year": year, "status_code": votes_status}},
                source="camara_dataset",
            )
            if votes_status == 200 and votes_text.strip():
                try:
                    votes_payload = json.loads(votes_text)
                except Exception:
                    votes_payload = []
                for row in self._iter_static_records(votes_payload):
                    row_date = self._coerce_date(
                        row.get("data")
                        or row.get("dataHoraRegistro")
                        or row.get("dataVotacao")
                        or row.get("dataHoraVotacao")
                    )
                    if row_date and (row_date < from_date or row_date > to_date):
                        continue
                    event_id = row.get("id") or row.get("idVotacao")
                    if not event_id:
                        continue
                    try:
                        node = normalize_vote_event(row)
                    except Exception:
                        continue
                    self.graph.upsert_vote_event(node, raw_votes_year.id)
                    event_node_by_votacao[str(event_id)] = node["id"]
                    events_count += 1

            if not votes_nominal_template:
                continue

            nominal_url = votes_nominal_template.format(year=year)
            nominal_status, nominal_text = self.client.get_text(nominal_url, raise_for_status=False)
            raw_nominal_year = self.raw_store.add_payload(
                batch=batch,
                endpoint=f"/datasets/votacoesVotos/{year}",
                params={"year": year, "url": nominal_url},
                primary_key=str(year),
                http_status=nominal_status,
                body_json={"metadata": {"url": nominal_url, "year": year, "status_code": nominal_status}},
                source="camara_dataset",
            )
            if nominal_status != 200 or not nominal_text.strip() or not event_node_by_votacao:
                continue
            try:
                nominal_payload = json.loads(nominal_text)
            except Exception:
                continue

            for row in self._iter_static_records(nominal_payload):
                votacao_id = row.get("idVotacao") or row.get("id")
                if not votacao_id:
                    continue
                event_node_id = event_node_by_votacao.get(str(votacao_id))
                if not event_node_id:
                    continue
                deputado_id = row.get("idDeputado") or row.get("deputado_", {}).get("id")
                if not deputado_id:
                    continue
                try:
                    dep_id_int = int(deputado_id)
                except Exception:
                    continue
                if selected_ids and dep_id_int not in selected_ids:
                    continue
                person_node_id = f"camara:person:{dep_id_int}"
                try:
                    action = normalize_vote_action(row, event_node_id, person_node_id)
                except Exception:
                    action = normalize_vote_action(
                        {"idDeputado": dep_id_int, "voto": row.get("voto") or row.get("tipoVoto")},
                        event_node_id,
                        person_node_id,
                    )
                self.graph.upsert_vote_action(action, raw_nominal_year.id)
                actions_count += 1

        return events_count, actions_count

    def _ingest_expenses_dataset_fallback(
        self,
        *,
        batch: Any,
        from_date: date,
        to_date: date,
        deputado_ids: list[int],
        coverage_gaps: list[dict[str, Any]],
    ) -> int:
        settings = get_settings()
        template = settings.camara_expenses_dataset_url_template.strip()
        if not template:
            return 0

        rows_processed = 0
        years = sorted({int(gap["year"]) for gap in coverage_gaps if gap.get("year")})
        dep_set = set(int(dep) for dep in deputado_ids)
        sep = settings.camara_expenses_dataset_separator or ","

        for year in years:
            url = template.format(year=year)
            status, csv_text = self.client.get_text(url, raise_for_status=False)
            raw = self.raw_store.add_payload(
                batch=batch,
                endpoint=f"/datasets/despesas/{year}",
                params={"year": year, "url": url},
                primary_key=str(year),
                http_status=status,
                body_json={"metadata": {"url": url, "year": year, "status_code": status}},
                source="camara_dataset",
            )
            if status != 200 or not csv_text.strip():
                continue

            reader = csv.DictReader(io.StringIO(csv_text), delimiter=sep)
            for row in reader:
                dep_id = self._dataset_dep_id(row)
                if dep_id is None or dep_id not in dep_set:
                    continue
                normalized = self._dataset_expense_to_camara_shape(row, dep_id, year)
                if not normalized:
                    continue
                node = normalize_expense(normalized, dep_id)
                self.graph.upsert_expense(node, raw.id)
                rows_processed += 1

        return rows_processed

    @staticmethod
    def _dataset_dep_id(row: dict[str, Any]) -> int | None:
        for key in ("idDeputado", "id_deputado", "ideCadastro", "ide_cadastro", "nuDeputadoId", "deputado_id"):
            value = row.get(key)
            if value in (None, ""):
                continue
            try:
                return int(str(value).strip())
            except Exception:
                continue
        return None

    @staticmethod
    def _dataset_expense_to_camara_shape(row: dict[str, Any], dep_id: int, year: int) -> dict[str, Any] | None:
        def _get(*keys: str) -> Any:
            for key in keys:
                if key in row and row.get(key) not in (None, ""):
                    return row.get(key)
            return None

        month = _get("mes", "month", "numMes", "nuMes")
        value = _get("valorDocumento", "valor_documento", "vlrDocumento", "valorLiquido", "vlrLiquido")
        supplier = _get("nomeFornecedor", "txtFornecedor", "fornecedor")
        cnpj_cpf = _get("cnpjCpfFornecedor", "cnpj_cpf_fornecedor", "cpfCnpjFornecedor")
        cod_documento = _get("codDocumento", "cod_documento", "documento")
        data_documento = _get("dataDocumento", "data_documento", "dtDocumento")
        tipo = _get("tipoDespesa", "tipo_despesa", "descricao")

        if value is None:
            return None

        return {
            "codDocumento": cod_documento or f"dataset:{dep_id}:{year}:{month}:{value}:{supplier}",
            "ano": year,
            "mes": month,
            "valorDocumento": value,
            "valorLiquido": value,
            "nomeFornecedor": supplier,
            "cnpjCpfFornecedor": cnpj_cpf,
            "dataDocumento": data_documento,
            "tipoDespesa": tipo,
        }
