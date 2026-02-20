from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("sqlalchemy")

from app.main import create_app


def test_interview_paths_exist_in_openapi():
    client = TestClient(create_app())
    spec = client.get("/openapi.json").json()

    paths = spec["paths"]
    assert "/api/v1/auth/token" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/interview/start" in paths
    assert "/api/v1/interview/{session_id}/answer" in paths
    assert "/api/v1/interview/{session_id}/finish" in paths
    assert "/api/v1/interview/{session_id}/export" in paths
    assert "/api/v1/budget/simulate" in paths
