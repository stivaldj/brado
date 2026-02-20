from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("sqlalchemy")

from app.core.config import get_settings
from app.main import create_app
from app.security.api_v1_auth import _RATE_BUCKETS


class _FakeService:
    def start_session(self, user_id=None, metadata=None):
        return {
            "session_id": "sess-1",
            "question": {
                "id": "ECO_001",
                "pergunta": "Pergunta",
                "tipo_resposta": "LIKERT_7",
                "dimensoes_afetadas": {"ECO": 1.0},
                "tags": ["eco"],
            },
        }

    def submit_answer(self, session_id, question_id, answer):
        return {"session_id": session_id, "answered_questions": 1, "next_question": None}

    def finish_session(self, session_id):
        return {
            "session_id": session_id,
            "resultado": {
                "vetor": {"ECO": 0.7, "SOC": 0.1, "EST": 0.2, "AMB": 0.2, "LIB": 0.1, "GOV": 0.3, "GLB": 0.4, "INS": 0.5},
                "esquerda_direita": 0.3,
                "confianca": 0.9,
                "consistencia": 0.8,
            },
            "ranking": [],
        }

    def get_result(self, session_id):
        return self.finish_session(session_id)

    def export_result_json(self, session_id):
        return self.finish_session(session_id)

    def export_result_pdf(self, session_id):
        return b"%PDF-1.4 fake"

    def run_budget_simulation(self, allocations):
        return {"valid": True, "total_percent": 100, "tradeoffs": []}

    def query_legislative_items(self, limit):
        return {"items": [{"id": 1, "ementa": "x"}]}

    def upsert_legislator_profiles(self, profiles):
        return {"upserted": len(profiles)}

    def upsert_party_profiles(self, profiles):
        return {"upserted": len(profiles)}


@pytest.fixture(autouse=True)
def _reset_settings_and_rate_buckets(monkeypatch):
    monkeypatch.setenv("API_V1_AUTH_REQUIRED", "false")
    monkeypatch.setenv("API_V1_RATE_LIMIT_PER_MINUTE", "120")
    get_settings.cache_clear()
    _RATE_BUCKETS.clear()
    yield
    get_settings.cache_clear()
    _RATE_BUCKETS.clear()


def test_interview_router_flow(monkeypatch):
    monkeypatch.setattr("app.api.routers.interview.service", _FakeService())
    client = TestClient(create_app())

    start = client.post("/api/v1/interview/start", json={"user_id": "u1", "metadata": {"lang": "pt"}})
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    answer = client.post(f"/api/v1/interview/{session_id}/answer", json={"question_id": "ECO_001", "answer": 6})
    assert answer.status_code == 200

    finish = client.post(f"/api/v1/interview/{session_id}/finish")
    assert finish.status_code == 200
    assert finish.json()["resultado"]["confianca"] == 0.9


def test_budget_and_legislative_routes(monkeypatch):
    monkeypatch.setattr("app.api.routers.interview.service", _FakeService())
    client = TestClient(create_app())

    budget = client.post(
        "/api/v1/budget/simulate",
        json={"allocations": [{"category": "saude", "percent": 50}, {"category": "educacao", "percent": 50}]},
    )
    assert budget.status_code == 200
    assert budget.json()["valid"] is True

    legislative = client.get("/api/v1/legislative/propositions?limit=5")
    assert legislative.status_code == 200
    assert legislative.json()["items"][0]["id"] == 1


def test_export_routes(monkeypatch):
    monkeypatch.setattr("app.api.routers.interview.service", _FakeService())
    client = TestClient(create_app())

    json_export = client.get("/api/v1/interview/sess-1/export?format=json")
    assert json_export.status_code == 200
    assert json_export.json()["session_id"] == "sess-1"

    pdf_export = client.get("/api/v1/interview/sess-1/export?format=pdf")
    assert pdf_export.status_code == 200
    assert pdf_export.headers["content-type"] == "application/pdf"


def test_interview_requires_bearer_when_enabled(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret-key")
    monkeypatch.setenv("API_V1_AUTH_REQUIRED", "true")
    get_settings.cache_clear()
    monkeypatch.setattr("app.api.routers.interview.service", _FakeService())
    client = TestClient(create_app())

    unauth = client.post("/api/v1/interview/start", json={"user_id": "u1", "metadata": {}})
    assert unauth.status_code == 401

    token_resp = client.post("/api/v1/auth/token", json={"client_id": "frontend"})
    assert token_resp.status_code == 200
    access_token = token_resp.json()["access_token"]

    auth = client.post(
        "/api/v1/interview/start",
        json={"user_id": "u1", "metadata": {}},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert auth.status_code == 200


def test_interview_rate_limit_by_session(monkeypatch):
    monkeypatch.setenv("API_V1_AUTH_REQUIRED", "true")
    monkeypatch.setenv("API_V1_RATE_LIMIT_PER_MINUTE", "1")
    get_settings.cache_clear()
    monkeypatch.setattr("app.api.routers.interview.service", _FakeService())
    client = TestClient(create_app())

    token_resp = client.post("/api/v1/auth/token", json={"client_id": "frontend"})
    assert token_resp.status_code == 200
    access_token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    first = client.post("/api/v1/interview/sess-1/answer", json={"question_id": "ECO_001", "answer": 6}, headers=headers)
    assert first.status_code == 200

    second = client.post("/api/v1/interview/sess-1/answer", json={"question_id": "ECO_001", "answer": 6}, headers=headers)
    assert second.status_code == 429
