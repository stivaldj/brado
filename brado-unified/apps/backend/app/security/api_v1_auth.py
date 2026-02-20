from __future__ import annotations

import base64
from collections import defaultdict, deque
import hashlib
import hmac
import json
import time
from typing import Deque, Dict, Tuple

from fastapi import Header, HTTPException, Request

from ..core.config import get_settings

_RATE_BUCKETS: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def issue_access_token(subject: str) -> dict[str, int | str]:
    settings = get_settings()
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + settings.api_v1_jwt_ttl_seconds,
        "scope": "api:v1",
    }
    token = _encode_jwt(payload, settings.api_v1_jwt_secret)
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.api_v1_jwt_ttl_seconds}


def require_api_v1_token(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> str:
    settings = get_settings()
    if not authorization:
        if settings.api_v1_auth_required:
            raise HTTPException(status_code=401, detail="Bearer token required")
        request.state.api_v1_payload = {"sub": "anonymous", "iat": 0, "exp": 0, "scope": "api:v1"}
        request.state.api_v1_subject = "anonymous"
        return "anonymous"

    payload = decode_authorization_payload(authorization)
    subject = str(payload.get("sub") or "anonymous")
    request.state.api_v1_payload = payload
    request.state.api_v1_subject = subject
    return subject


def decode_authorization_payload(authorization: str) -> dict:
    settings = get_settings()
    token_type, token = _parse_authorization_header(authorization)
    if token_type != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    try:
        payload = _decode_jwt(token, settings.api_v1_jwt_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return payload


def enforce_session_rate_limit(request: Request, session_id: str) -> None:
    settings = get_settings()
    now = time.time()
    client_ip = request.client.host if request.client else "unknown"
    key = (client_ip, session_id)
    bucket = _RATE_BUCKETS[key]

    while bucket and now - bucket[0] > 60:
        bucket.popleft()

    if len(bucket) >= settings.api_v1_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded for session")

    bucket.append(now)


def _parse_authorization_header(raw: str) -> tuple[str, str]:
    parts = raw.strip().split(" ", 1)
    if len(parts) != 2:
        return "", ""
    return parts[0].strip().lower(), parts[1].strip()


def _encode_jwt(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url(json.dumps(header, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    encoded_payload = _b64url(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")

    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = _b64url(signature)
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def _decode_jwt(token: str, secret: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid bearer token")

    encoded_header, encoded_payload, encoded_signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature = _b64url_decode(encoded_signature)

    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid bearer token")

    payload_raw = _b64url_decode(encoded_payload)
    payload = json.loads(payload_raw.decode("utf-8"))

    exp = int(payload.get("exp", 0))
    if exp <= int(time.time()):
        raise ValueError("Bearer token expired")

    return payload


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))
