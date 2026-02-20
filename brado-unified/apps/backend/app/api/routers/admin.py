from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from ...auth import require_admin_api_key
from ...jobs.orchestrator import JobOrchestrator

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_api_key)])


@router.post("/ingest/all")
def ingest_all(from_date: date = Query(default=date(2018, 1, 1), alias="from")) -> dict:
    return JobOrchestrator().ingest_all(from_date)


@router.post("/ingest/deputados")
def ingest_deputados() -> dict:
    return JobOrchestrator().ingest_deputados()


@router.post("/ingest/bills")
def ingest_bills(from_date: date = Query(default=date(2018, 1, 1), alias="from")) -> dict:
    return JobOrchestrator().ingest_bills(from_date)


@router.post("/ingest/votes")
def ingest_votes(from_date: date = Query(default=date(2018, 1, 1), alias="from")) -> dict:
    return JobOrchestrator().ingest_votes(from_date)


@router.post("/ingest/expenses")
def ingest_expenses(from_date: date = Query(default=date(2018, 1, 1), alias="from")) -> dict:
    return JobOrchestrator().ingest_expenses(from_date)


@router.post("/reconcile/all")
def reconcile_all() -> dict:
    return JobOrchestrator().reconcile_all()


@router.get("/reconcile/latest")
def reconcile_latest() -> dict:
    return JobOrchestrator().latest_reconcile_report()


@router.get("/job_state")
def job_state(limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> dict:
    return JobOrchestrator().list_job_state(limit=limit, offset=offset)


@router.post("/profiles/refresh")
def refresh_profiles(limit_payloads: int = Query(default=500, ge=1, le=2000)) -> dict:
    return JobOrchestrator().refresh_political_profiles(limit_payloads=limit_payloads)
