from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("sqlalchemy")

from app.main import create_app


def test_admin_job_state_requires_api_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    from app.core.config import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    response = client.get("/admin/job_state")
    assert response.status_code == 401


def test_admin_job_state_returns_paginated_payload(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    from app.core.config import get_settings

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    monkeypatch.setattr(
        "app.api.routers.admin.JobOrchestrator.list_job_state",
        lambda self, limit=20, offset=0: {
            "limit": limit,
            "offset": offset,
            "job_state": [{"job_name": "ingest_expenses_since", "status": "running", "cursor_json": {}, "updated_at": None}],
            "reconcile_reports": [{"id": "r1", "status": "success", "run_at": None, "report": {}}],
        },
    )

    response = client.get("/admin/job_state?limit=5&offset=10", headers={"X-API-Key": "secret-key"})
    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 5
    assert body["offset"] == 10
    assert body["job_state"][0]["job_name"] == "ingest_expenses_since"
