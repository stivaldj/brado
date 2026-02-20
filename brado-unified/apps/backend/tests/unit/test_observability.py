from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("sqlalchemy")

from app.main import create_app


def test_metrics_endpoint_exposes_prometheus_text(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    from app.core.config import get_settings

    get_settings.cache_clear()
    client = TestClient(create_app())

    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "brado_http_requests_total" in response.text
    assert "brado_http_request_latency_seconds_bucket" in response.text


def test_trace_headers_are_returned(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    from app.core.config import get_settings

    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id")
    assert response.headers.get("traceparent")
