"""FastAPI app for tests: no lifespan (avoids HF prompt guard + full bootstrap on every client)."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.api import api_router
from app.config.settings import get_settings
from app.core.logging_config import configure_logging, reset_logging_for_tests
from app.core.rate_limit import install_rate_limits


def create_test_app() -> FastAPI:
    reset_logging_for_tests()
    configure_logging(get_settings())
    app = FastAPI(title="Career Copilot (test)")
    install_rate_limits(app)
    app.include_router(api_router)
    return app
