"""ASGI entry: ``app`` is the FastAPI instance (e.g. ``uvicorn app.main:app``); CLI uses ``main()`` below."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

from app.api.api import api_router
from app.config.settings import get_settings
from app.core.bootstrap import init_app, shutdown_app, verify_database_connection
from app.core.logging_config import configure_logging
from app.core.rate_limit import install_rate_limits
from app.core.request_logging import RequestLoggingMiddleware

_lifecycle_log = logging.getLogger("app.lifecycle")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if not settings.database_url:
        msg = "DATABASE_URL is required to run the HTTP API."
        _lifecycle_log.error(
            msg,
            extra={"event": "lifecycle_startup_config_error", "error_code": "database_url_missing"},
        )
        raise RuntimeError(msg)
    _lifecycle_log.info(
        "Application startup: initializing core services",
        extra={"event": "lifecycle_startup_begin"},
    )
    try:
        init_app()
        verify_database_connection()
    except Exception:
        _lifecycle_log.exception(
            "Application startup failed",
            extra={"event": "lifecycle_startup_failed"},
        )
        raise
    _lifecycle_log.info(
        "Application startup complete",
        extra={"event": "lifecycle_startup_ready"},
    )
    yield
    _lifecycle_log.info(
        "Application shutdown: releasing resources",
        extra={"event": "lifecycle_shutdown_begin"},
    )
    try:
        shutdown_app()
    except Exception:
        _lifecycle_log.exception(
            "Application shutdown raised an error",
            extra={"event": "lifecycle_shutdown_error"},
        )
        raise
    _lifecycle_log.info(
        "Application shutdown complete",
        extra={"event": "lifecycle_shutdown_complete"},
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    _lifecycle_log.info(
        "Creating FastAPI application",
        extra={
            "event": "lifecycle_create_app",
            "app_name": settings.app_name,
            "debug": settings.debug,
        },
    )
    application = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    install_rate_limits(application)
    if settings.cors_allow_origins:
        # Parse CSV origins string into list
        origins = [x.strip() for x in settings.cors_allow_origins.split(",") if x.strip()]
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    application.add_middleware(RequestLoggingMiddleware)
    application.include_router(api_router)
    return application


app = create_app()


def main() -> None:
    """CLI: run one career workflow turn (requires LLM and search keys as configured)."""
    from app.pipeline import run_turn

    out = run_turn("I'm a backend dev — should I move into AI?")
    for key in ("plan", "research", "analysis", "critique", "synthesis"):
        print(f"\n=== {key} ===\n{out.get(key)}")


if __name__ == "__main__":
    main()
