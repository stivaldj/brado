from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .context import (
    clear_trace_context,
    generate_span_id,
    generate_trace_id,
    set_trace_context,
)
from .metrics import metrics_registry

logger = logging.getLogger("app.observability")


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("traceparent", "")
        trace_id = _extract_trace_id(incoming) or generate_trace_id()
        span_id = generate_span_id()
        set_trace_context(trace_id, span_id)

        start = time.perf_counter()
        status = 500
        route = request.url.path

        try:
            logger.info("request_started")
            response = await call_next(request)
            status = int(response.status_code)
            if request.scope.get("route") and getattr(request.scope["route"], "path", None):
                route = str(request.scope["route"].path)
            response.headers["X-Trace-Id"] = trace_id
            response.headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
            return response
        finally:
            elapsed = time.perf_counter() - start
            metrics_registry.observe_request(method=request.method, route=route, status=status, latency_seconds=elapsed)
            logger.info("request_finished")
            clear_trace_context()


def _extract_trace_id(traceparent: str) -> str | None:
    parts = traceparent.split("-")
    if len(parts) != 4:
        return None
    trace_id = parts[1].strip().lower()
    if len(trace_id) != 32:
        return None
    return trace_id
