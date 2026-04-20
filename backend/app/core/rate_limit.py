"""SlowAPI rate limits: per-IP for unauthenticated routes, per bearer session for authenticated ones."""

from __future__ import annotations

import hashlib
import logging

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def _rate_limit_key(request: Request) -> str:
    """Prefer stable key from Authorization header (hashed); else client IP."""
    if not get_settings().rate_limit_enabled:
        return f"off:{get_remote_address(request)}"
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer ") and len(auth) > 20:
        digest = hashlib.sha256(auth.encode("utf-8")).hexdigest()[:48]
        return f"bearer:{digest}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_rate_limit_key)


def _effective(spec: str) -> str:
    return spec if get_settings().rate_limit_enabled else "999999/minute"


def limit_login() -> str:
    return _effective(get_settings().rate_limit_login)


def limit_register() -> str:
    return _effective(get_settings().rate_limit_register)


def limit_auth_email() -> str:
    return _effective(get_settings().rate_limit_auth_email)


def limit_verify_email_get() -> str:
    return _effective(get_settings().rate_limit_verify_email_get)


def limit_reset_password() -> str:
    return _effective(get_settings().rate_limit_reset_password)


def limit_profile() -> str:
    return _effective(get_settings().rate_limit_profile)


def limit_workflow_stream() -> str:
    return _effective(get_settings().rate_limit_workflow_stream)


def limit_health() -> str:
    return _effective(get_settings().rate_limit_health)


def install_rate_limits(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting installed (enabled=%s)", get_settings().rate_limit_enabled)
