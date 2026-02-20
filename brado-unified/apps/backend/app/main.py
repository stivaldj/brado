from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers.admin import router as admin_router
from .api.routers.auth_v1 import router as auth_v1_router
from .api.routers.health import router as health_router
from .api.routers.interview import router as interview_router
from .api.routers.observability import router as observability_router
from .core.config import get_settings
from .core.logging import configure_logging
from .core.observability.middleware import RequestObservabilityMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version="1.0.0")
    allow_all = "*" in settings.cors_allow_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else list(settings.cors_allow_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestObservabilityMiddleware)
    app.include_router(health_router)
    app.include_router(observability_router)
    app.include_router(auth_v1_router)
    app.include_router(admin_router)
    app.include_router(interview_router)
    return app


app = create_app()
