from __future__ import annotations

from fastapi import APIRouter, Response

from ...core.observability.metrics import metrics_registry

router = APIRouter(tags=["observability"])


@router.get("/metrics")
def metrics() -> Response:
    return Response(content=metrics_registry.render_prometheus_text(), media_type="text/plain; version=0.0.4")


@router.get("/ready")
def ready() -> dict:
    return {"status": "ready"}
