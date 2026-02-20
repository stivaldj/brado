from __future__ import annotations

import time

from app.security import api_v1_auth


def test_issue_and_decode_access_token(monkeypatch):
    monkeypatch.setenv("API_V1_JWT_SECRET", "secret-123")
    monkeypatch.setenv("API_V1_JWT_TTL_SECONDS", "3600")

    from app.core.config import get_settings

    get_settings.cache_clear()
    token_data = api_v1_auth.issue_access_token("web-client")

    payload = api_v1_auth._decode_jwt(token_data["access_token"], "secret-123")
    assert payload["sub"] == "web-client"
    assert payload["exp"] > payload["iat"]


def test_decode_rejects_expired_token(monkeypatch):
    monkeypatch.setenv("API_V1_JWT_SECRET", "secret-123")
    from app.core.config import get_settings

    get_settings.cache_clear()
    expired = api_v1_auth._encode_jwt(
        {
            "sub": "client",
            "iat": int(time.time()) - 100,
            "exp": int(time.time()) - 1,
        },
        "secret-123",
    )

    try:
        api_v1_auth._decode_jwt(expired, "secret-123")
    except ValueError as exc:
        assert str(exc) == "Bearer token expired"
    else:
        raise AssertionError("expected ValueError for expired token")


def test_parse_authorization_header():
    token_type, token = api_v1_auth._parse_authorization_header("Bearer abc.def")
    assert token_type == "bearer"
    assert token == "abc.def"
