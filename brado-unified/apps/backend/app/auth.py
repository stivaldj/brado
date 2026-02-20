from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Header, HTTPException, Request

from .core.config import get_settings

_BUCKETS: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def _enforce_rate_limit(client_ip: str, api_key: str) -> None:
    settings = get_settings()
    now = time.time()
    key = (client_ip, api_key)
    bucket = _BUCKETS[key]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= settings.admin_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)


def require_admin_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    settings = get_settings()
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    client_ip = request.client.host if request.client else "unknown"
    _enforce_rate_limit(client_ip, x_api_key)
    return x_api_key
