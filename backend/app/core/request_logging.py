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
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            logger.exception(
                "HTTP request failed",
                extra={
                    "event": "http_request_error",
                    "http_method": method,
                    "http_path": path,
                    "user_id": uid_log,
                    "duration_ms": duration_ms,
                },
            )
            raise
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        status = response.status_code
        base_extra = {
            "event": "http_request",
            "http_method": method,
            "http_path": path,
            "user_id": uid_log,
            "http_status": status,
            "duration_ms": duration_ms,
        }
        if path == "/health":
            logger.debug("HTTP request", extra={**base_extra, "event": "http_request_health"})
        elif status >= 500:
            logger.error("HTTP request server error", extra={**base_extra, "http_outcome": "server_error"})
        elif status >= 400:
            logger.warning("HTTP request client error", extra={**base_extra, "http_outcome": "client_error"})
        else:
            logger.info("HTTP request ok", extra={**base_extra, "http_outcome": "ok"})
        return response
