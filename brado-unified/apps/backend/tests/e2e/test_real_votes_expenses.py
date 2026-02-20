from __future__ import annotations

import os
from datetime import date

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("neo4j")

from neo4j import GraphDatabase
from sqlalchemy import text

from app.core.config import get_settings
from app.db.sql import SessionLocal
from app.jobs.ingest_jobs import IngestJobs
from app.reconcile.service import ReconcileService


pytestmark = pytest.mark.e2e


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


def _requires_real_env() -> None:
    settings = get_settings()
    if os.getenv("RUN_REAL_E2E") != "1":
        pytest.skip("Set RUN_REAL_E2E=1 to execute real e2e tests")
    if settings.vcr_mode not in {"record", "replay"}:
        pytest.skip("Set VCR_MODE=record or VCR_MODE=replay")
    if not _can_connect_postgres():
        pytest.skip("Postgres not available")
    if not _can_connect_neo4j():
        pytest.skip("Neo4j not available")


def test_smoke_real_votes_expenses():
    _requires_real_env()

    with SessionLocal() as session:
        jobs = IngestJobs(session)
        try:
            smoke = jobs.smoke_real(sample_size=5)
            reconcile = ReconcileService(session)
            try:
                report = reconcile.reconcile_all()
            finally:
                reconcile.close()
        finally:
            jobs.close()

        assert len(smoke["selected_deputados"]) == 5
        assert smoke["expenses_recent"]["status"] == "success"
        assert smoke["expenses_recent"]["coverage_gaps"] == []
        assert report.status == "success"


def test_backfill_sample_2018():
    _requires_real_env()

    with SessionLocal() as session:
        jobs = IngestJobs(session)
        try:
            jobs.ingest_deputados_current(max_pages=2)
            bills = jobs.ingest_bills_since(date(2018, 1, 1), to_date=date(2018, 12, 31), max_pages=2)
            votes = jobs.ingest_votes_since(date(2018, 1, 1), to_date=date(2018, 12, 31), max_pages=2)

            reconcile = ReconcileService(session)
            try:
                report = reconcile.reconcile_all()
            finally:
                reconcile.close()
        finally:
            jobs.close()

        assert bills["status"] == "success"
        assert votes["status"] == "success"
        assert "checks" in report.report
        uniqueness_checks = [c for c in report.report["checks"] if c["name"].startswith("uniqueness_")]
        assert uniqueness_checks and all(check["ok"] for check in uniqueness_checks)
