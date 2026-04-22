"""Central logging setup for the backend (console, optional rotating file, UTC timestamps)."""

from __future__ import annotations

import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from logging import LogRecord
from pathlib import Path

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

    formatter = _UtcFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(stderr_handler)

    if s.log_file_enabled and (s.log_file_dir or "").strip():
        log_dir = Path(s.log_file_dir).expanduser()
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "app.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError as exc:
            sys.stderr.write(f"WARNING: could not open log file under {log_dir}: {exc}\n")

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
    """Clear handlers and idempotency flag (tests only)."""
    global _configured
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
        try:
            h.close()
        except OSError:
            pass
    _configured = False
