from __future__ import annotations

from datetime import date

from sqlalchemy import select

from ..db.sql import session_scope
from ..db.sql.models import JobState, ReconcileReport
from ..jobs.ingest_jobs import IngestJobs
from ..jobs.profile_jobs import ProfileJobs
from ..reconcile.service import ReconcileService


class JobOrchestrator:
    def ingest_deputados(self) -> dict:
        with session_scope() as session:
            jobs = IngestJobs(session)
            try:
                return jobs.ingest_deputados_current()
            finally:
                jobs.close()

    def ingest_bills(self, from_date: date) -> dict:
        with session_scope() as session:
            jobs = IngestJobs(session)
            try:
                return jobs.ingest_bills_since(from_date)
            finally:
                jobs.close()

    def ingest_votes(self, from_date: date) -> dict:
        with session_scope() as session:
            jobs = IngestJobs(session)
            try:
                return jobs.ingest_votes_since(from_date)
            finally:
                jobs.close()

    def ingest_expenses(self, from_date: date) -> dict:
        with session_scope() as session:
            jobs = IngestJobs(session)
            try:
                return jobs.ingest_expenses_since(from_date)
            finally:
                jobs.close()

    def ingest_all(self, from_date: date) -> dict:
        return {
            "deputados": self.ingest_deputados(),
            "bills": self.ingest_bills(from_date),
            "votes": self.ingest_votes(from_date),
            "expenses": self.ingest_expenses(from_date),
        }

    def reconcile_all(self) -> dict:
        with session_scope() as session:
            reconcile = ReconcileService(session)
            try:
                result = reconcile.reconcile_all()
                if result.status != "success":
                    raise RuntimeError(result.report)
                return result.report
            finally:
                reconcile.close()

    def latest_reconcile_report(self) -> dict:
        with session_scope() as session:
            row = session.execute(select(ReconcileReport).order_by(ReconcileReport.run_at.desc()).limit(1)).scalar_one_or_none()
            if not row:
                return {"status": "not_found"}
            return {"id": row.id, "run_at": row.run_at.isoformat(), "status": row.status, "report": row.report_json}

    def list_job_state(self, limit: int = 20, offset: int = 0) -> dict:
        page_limit = max(1, min(limit, 100))
        page_offset = max(0, offset)
        with session_scope() as session:
            states = (
                session.execute(select(JobState).order_by(JobState.updated_at.desc()).offset(page_offset).limit(page_limit))
                .scalars()
                .all()
            )
            reports = (
                session.execute(
                    select(ReconcileReport).order_by(ReconcileReport.run_at.desc()).offset(page_offset).limit(page_limit)
                )
                .scalars()
                .all()
            )
            return {
                "limit": page_limit,
                "offset": page_offset,
                "job_state": [
                    {
                        "job_name": row.job_name,
                        "status": row.status,
                        "cursor_json": row.cursor_json or {},
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    }
                    for row in states
                ],
                "reconcile_reports": [
                    {
                        "id": row.id,
                        "run_at": row.run_at.isoformat() if row.run_at else None,
                        "status": row.status,
                        "report": row.report_json,
                    }
                    for row in reports
                ],
            }

    def smoke_real(self, sample_size: int = 5) -> dict:
        with session_scope() as session:
            jobs = IngestJobs(session)
            try:
                result = jobs.smoke_real(sample_size=sample_size)
            finally:
                jobs.close()
        result["reconcile"] = self.reconcile_all()
        return result

    def refresh_political_profiles(self, limit_payloads: int = 500) -> dict:
        with session_scope() as session:
            jobs = ProfileJobs(session)
            return jobs.refresh_from_raw_votes(limit_payloads=limit_payloads)
