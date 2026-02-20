from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from ...political_interview.schemas import ApiV1TokenRequest, ApiV1TokenResponse
from ...security.api_v1_auth import issue_access_token, require_api_v1_token

router = APIRouter(prefix="/api/v1/auth", tags=["api-v1-auth"])


@router.post("/token", response_model=ApiV1TokenResponse)
def create_token(request: ApiV1TokenRequest) -> dict:
    return issue_access_token(subject=request.client_id)


@router.get("/me", dependencies=[Depends(require_api_v1_token)])
def whoami(request: Request) -> dict:
    payload = getattr(request.state, "api_v1_payload", {"sub": "anonymous", "exp": 0, "scope": "api:v1"})
    now = int(time.time())
    exp = int(payload.get("exp", 0))
    expires_in = max(0, exp - now) if exp > 0 else 0
    return {
        "subject": payload.get("sub", "anonymous"),
        "scope": payload.get("scope", "api:v1"),
        "expires_at": exp,
        "expires_in": expires_in,
        "authenticated": expires_in > 0,
    }
