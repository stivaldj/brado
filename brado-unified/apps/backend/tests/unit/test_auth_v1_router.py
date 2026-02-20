from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("sqlalchemy")

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch):
    monkeypatch.setenv("API_V1_AUTH_REQUIRED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_auth_me_requires_token():
    client = TestClient(create_app())
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_me_returns_subject_and_ttl():
    client = TestClient(create_app())
    token_resp = client.post("/api/v1/auth/token", json={"client_id": "frontend-ui"})
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["subject"] == "frontend-ui"
    assert body["authenticated"] is True
    assert body["expires_in"] > 0
