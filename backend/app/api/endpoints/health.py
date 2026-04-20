"""Liveness / readiness for the process and critical dependencies."""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.core.rate_limit import limiter, limit_health
from app.db.session import database_health
from app.guardrails.prompt_guard import is_prompt_guard_loaded

logger = logging.getLogger(__name__)

router = APIRouter()


def _app_version() -> str:
    try:
        from importlib.metadata import version

        return version("career-copilot")
    except Exception:  # noqa: BLE001
        return "0.1.0"


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"] = Field(description="Aggregate process health.")
    version: str
    app_name: str
    checks: dict[str, Any] = Field(description="Per-dependency status: ok | not_configured | error + optional detail.")


@router.get("/health", response_model=HealthResponse)
@limiter.limit(limit_health)
def get_health(request: Request) -> HealthResponse:
    _ = request.app
    """
    Public endpoint: database connectivity (when configured) and prompt-guard load state.
    ``degraded``: optional components missing (e.g. DB not configured in dev); ``unhealthy``: DB configured but failing.
    """
    settings = get_settings()
    checks: dict[str, Any] = {}

    db_state, db_err = database_health()
    checks["database"] = {"status": db_state, "detail": db_err}

    pg_ok = is_prompt_guard_loaded()
    checks["prompt_guard"] = {"status": "ok" if pg_ok else "not_ready"}

    if db_state == "error":
        overall: Literal["healthy", "degraded", "unhealthy"] = "unhealthy"
    elif db_state == "not_configured" or not pg_ok:
        overall = "degraded"
    else:
        overall = "healthy"

    body = HealthResponse(
        status=overall,
        version=_app_version(),
        app_name=settings.app_name,
        checks=checks,
    )
    if overall == "unhealthy":
        logger.error("Health check unhealthy: %s", checks)
    return body
