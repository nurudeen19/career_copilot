"""HTTP middleware: request timing, status, and uncaught exceptions."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.request_identity import jwt_sub_for_logs

logger = logging.getLogger("app.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.perf_counter()
        path = request.url.path
        method = request.method
        user_id = jwt_sub_for_logs(request)
        uid_log = user_id or "-"
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s user_id=%s failed after %.1f ms",
                method,
                path,
                uid_log,
                duration_ms,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        status = response.status_code
        if path == "/health":
            logger.debug(
                "%s %s user_id=%s -> %s in %.1f ms",
                method,
                path,
                uid_log,
                status,
                duration_ms,
            )
        elif status >= 500:
            logger.error(
                "%s %s user_id=%s -> %s in %.1f ms",
                method,
                path,
                uid_log,
                status,
                duration_ms,
            )
        elif status >= 400:
            logger.warning(
                "%s %s user_id=%s -> %s in %.1f ms",
                method,
                path,
                uid_log,
                status,
                duration_ms,
            )
        else:
            logger.info(
                "%s %s user_id=%s -> %s in %.1f ms",
                method,
                path,
                uid_log,
                status,
                duration_ms,
            )
        return response
