"""Central logging setup for the backend (console, UTC timestamps, uvicorn alignment)."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from logging import LogRecord

from app.config.settings import Settings

_configured = False


class _UtcFormatter(logging.Formatter):
    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def configure_logging(settings: Settings | None = None) -> None:
    """
    Configure the root logger once (idempotent). Call from ``create_app`` before other setup.
    """
    global _configured
    if _configured:
        return

    s = settings
    if s is None:
        from app.config.settings import get_settings

        s = get_settings()

    level_name = (s.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        _UtcFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).setLevel(level)

    # Reduce noisy third-party INFO unless debugging
    if level > logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    _configured = True
    logging.getLogger(__name__).debug("Logging configured at %s", level_name)


def reset_logging_for_tests() -> None:
    """Clear idempotency flag (tests only)."""
    global _configured
    _configured = False
