"""SlowAPI rate limits."""

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
    if not get_settings().rate_limits.enabled:
        return f"off:{get_remote_address(request)}"
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer ") and len(auth) > 20:
        digest = hashlib.sha256(auth.encode("utf-8")).hexdigest()[:48]
        return f"bearer:{digest}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_rate_limit_key)


def _effective(spec: str) -> str:
    return spec if get_settings().rate_limits.enabled else "999999/minute"


def limit_login() -> str:
    return _effective(get_settings().rate_limits.login)


def limit_register() -> str:
    return _effective(get_settings().rate_limits.signup)


def limit_auth_email() -> str:
    return _effective(get_settings().rate_limits.auth_email)


def limit_verify_email() -> str:
    return _effective(get_settings().rate_limits.verify_email)


def limit_reset_password() -> str:
    return _effective(get_settings().rate_limits.reset_password)


def limit_profile() -> str:
    return _effective(get_settings().rate_limits.profile)


def limit_workflow_stream() -> str:
    return _effective(get_settings().rate_limits.workflow_stream)


def limit_health() -> str:
    return _effective(get_settings().rate_limits.health)


def install_rate_limits(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting installed (enabled=%s)", get_settings().rate_limits.enabled)
