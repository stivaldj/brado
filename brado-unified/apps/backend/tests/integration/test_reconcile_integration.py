import uuid
from datetime import date, datetime, timedelta, timezone
import time

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("neo4j")

from neo4j import GraphDatabase
from sqlalchemy import text

from app.core.config import get_settings
from app.db.raw_store import RawStore
from app.db.sql import SessionLocal
from app.db.sql.models import IngestionBatch, RawPayload, ReconcileReport
from app.graph.neo4j.writer import Neo4jWriter
from app.jobs.ingest_jobs import IngestJobs
from app.reconcile.service import ReconcileService


def _can_connect_postgres() -> bool:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _can_connect_neo4j() -> bool:
    settings = get_settings()
    try:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.integration


@pytest.fixture()
def integration_env():
    if not _can_connect_postgres() or not _can_connect_neo4j():
        pytest.skip("Postgres/Neo4j not available for integration test")

    settings = get_settings()
    writer = Neo4jWriter()
    writer.ensure_constraints()

    with writer.client.driver.session() as neo_session:
        neo_session.run(
            """
            MATCH (n)
            WHERE any(lbl IN labels(n) WHERE lbl IN ['Person','Bill','VoteEvent','VoteAction','Expense','Organization','Party','State','Committee'])
            DETACH DELETE n
            """
        )

    with SessionLocal() as session:
        session.execute(text("DELETE FROM reconcile_reports"))
        session.execute(text("DELETE FROM raw_payloads"))
        session.execute(text("DELETE FROM ingestion_batches"))
        session.commit()

    yield {"settings": settings}

    writer.close()


@pytest.fixture()
def db_session(integration_env):
    with SessionLocal() as session:
        yield session


def test_integrity_checks_detect_orphans(db_session):
    writer = Neo4jWriter()
    writer.ensure_constraints()

    person = {"id": "camara:person:9001", "sourceId": 9001, "name": "Teste"}
    bill = {"id": "camara:bill:7001", "sourceId": 7001, "ano": 2025, "numero": 1}
    vote_event = {
        "id": "camara:vote_event:5001",
        "sourceId": 5001,
        "dataHoraRegistro": "2025-01-10T10:00:00",
        "billId": bill["id"],
    }
    vote_action = {
        "id": "camara:vote_action:camara:vote_event:5001:camara:person:9001",
        "voteEventId": vote_event["id"],
        "personId": person["id"],
        "position": "Sim",
    }

    writer.upsert_person(person)
    writer.upsert_bill(bill)
    writer.upsert_vote_event(vote_event)
    writer.upsert_vote_action(vote_action)

    svc = ReconcileService(db_session)
    checks_ok = svc._integrity_checks()
    assert all(item["ok"] for item in checks_ok)

    with writer.client.driver.session() as neo_session:
        neo_session.run("MERGE (:VoteAction {id:'camara:vote_action:orphan'})").consume()

    checks_after = []
    for _ in range(10):
        checks_after = svc._integrity_checks()
        target = next(item for item in checks_after if item["name"] == "integrity_vote_action_has_event")
        if target["counts_actual"] >= 1:
            break
        time.sleep(0.1)
    target = next(item for item in checks_after if item["name"] == "integrity_vote_action_has_event")
    assert target["ok"] is False
    assert target["counts_actual"] >= 1

    svc.close()
    writer.close()


def test_temporal_checks_fail_when_raw_outside_batch_range(db_session):
    batch = IngestionBatch(
        id=str(uuid.uuid4()),
        source="camara",
        batch_type="camara:test:temporal",
        range_start=date(2025, 1, 1),
        range_end=date(2025, 1, 31),
        status="success",
        item_count=1,
    )
    db_session.add(batch)
    db_session.flush()

    raw = RawPayload(
        id=str(uuid.uuid4()),
        source="camara",
        endpoint="/test",
        params_json={},
        primary_key_value="1",
        fetched_at=datetime(2025, 2, 15, tzinfo=timezone.utc),
        http_status=200,
        url="/test",
        sha256="a" * 64,
        body_json={"dados": {"id": 1}},
        batch_id=batch.id,
    )
    db_session.add(raw)
    db_session.commit()

    svc = ReconcileService(db_session)
    checks = svc._temporal_checks()
    assert checks[0]["name"] == "temporal_batch_fetched_at_consistent"
    assert checks[0]["ok"] is False
    assert checks[0]["counts_actual"] >= 1
    svc.close()


def test_reconcile_all_persists_report_success(db_session):
    batch = IngestionBatch(
        id=str(uuid.uuid4()),
        source="camara",
        batch_type="camara:test:reconcile",
        range_start=date.today() - timedelta(days=1),
        range_end=date.today(),
        status="success",
        item_count=1,
    )
    db_session.add(batch)
    db_session.flush()

    raw = RawPayload(
        id=str(uuid.uuid4()),
        source="camara",
        endpoint="/test",
        params_json={},
        primary_key_value="1",
        fetched_at=datetime.now(timezone.utc),
        http_status=200,
        url="/test",
        sha256="b" * 64,
        body_json={"dados": {"id": 1}},
        batch_id=batch.id,
    )
    db_session.add(raw)
    db_session.commit()

    svc = ReconcileService(db_session)
    svc._coverage_checks = lambda: ([{"name": "coverage_stub", "ok": True}], [])
    svc._integrity_checks = lambda: [{"name": "integrity_stub", "ok": True}]
    svc._uniqueness_checks = lambda: [{"name": "uniq_stub", "ok": True}]
    svc._temporal_checks = lambda: [{"name": "temporal_stub", "ok": True}]
    svc._audit_samples = lambda _label, _limit=50: {"label": _label, "checked": 1, "mismatches": 0, "ok": True}

    result = svc.reconcile_all()
    assert result.status == "success"

    persisted = db_session.execute(text("SELECT count(*) FROM reconcile_reports")).scalar_one()
    assert int(persisted) >= 1

    row = db_session.query(ReconcileReport).order_by(ReconcileReport.run_at.desc()).first()
    assert row is not None
    assert row.status == "success"
    svc.close()


def test_ingest_votes_nominal_fallback_persists_real_404_and_500(db_session):
    class _FakeGraph:
        def close(self):
            return None

        def upsert_vote_event(self, *_args, **_kwargs):
            return None

        def upsert_vote_action(self, *_args, **_kwargs):
            return None

    class _FakeClient:
        def close(self):
            return None

        def paginated(self, endpoint, params=None, max_pages=None):
            assert endpoint == "/votacoes"
            yield 200, {"dados": [{"id": 9001}, {"id": 9002}], "links": []}, {"pagina": 1, "itens": 100}

        def fetch_many(self, requests, *, max_workers=None, raise_for_status=True):
            result = []
            for endpoint, _ in requests:
                if endpoint.endswith("/votos"):
                    if endpoint == "/votacoes/9001/votos":
                        result.append((404, {"dados": []}))
                    elif endpoint == "/votacoes/9002/votos":
                        result.append((500, {"erro": "failure"}))
                else:
                    result.append((200, {"dados": {"id": int(endpoint.split("/")[2]), "idProposicao": None}}))
            return result

    jobs = IngestJobs.__new__(IngestJobs)
    jobs.session = db_session
    jobs.raw_store = RawStore(db_session)
    jobs.client = _FakeClient()
    jobs.graph = _FakeGraph()
    jobs._max_workers = 4

    result = jobs.ingest_votes_since(date(2024, 1, 1), to_date=date(2024, 1, 10), max_pages=1)
    assert result["events"] == 2
    assert result["actions"] == 0

    rows = (
        db_session.query(RawPayload)
        .filter(RawPayload.endpoint.in_(( "/votacoes/9001/votos", "/votacoes/9002/votos")))
        .order_by(RawPayload.endpoint.asc())
        .all()
    )
    assert len(rows) == 2
    assert rows[0].http_status == 404
    assert rows[0].body_json["metadata"]["error_type"] == "nominal_votes_not_available"
    assert rows[1].http_status == 500
    assert rows[1].body_json["metadata"]["error_type"] == "upstream_error"


def test_reconcile_reports_coverage_fail_issue_type(db_session, monkeypatch):
    svc = ReconcileService(db_session)

    def _fake_paginated(endpoint, params=None, max_pages=None):
        if endpoint == "/deputados":
            yield 200, {"dados": [{"id": 1}, {"id": 2}], "links": []}, {"pagina": 1, "itens": 100}
            return
        raise AssertionError(endpoint)

    def _fake_get(endpoint, params=None, raise_for_status=True):
        if endpoint == "/proposicoes":
            return 200, {"dados": [], "links": []}
        if endpoint == "/votacoes":
            return 200, {"dados": [], "links": []}
        return 200, {"dados": [], "links": []}

    monkeypatch.setattr(svc.client, "paginated", _fake_paginated)
    monkeypatch.setattr(svc.client, "get", _fake_get)

    result = svc.reconcile_all()
    assert result.status == "failed"
    assert any(issue["issue_type"] == "coverage_deputados" for issue in result.report["issues"])
    svc.close()
