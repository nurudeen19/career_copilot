"""Central logging: colored human console + optional JSON file (or JSON everywhere if configured)."""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from logging import LogRecord
from pathlib import Path
from typing import Any

import colorlog

from app.config.settings import Settings

_configured = False

# LogRecord attributes to exclude when merging ``extra=`` into JSON (avoid collisions / noise).
_JSON_MERGE_SKIP: frozenset[str] = frozenset(
    {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "thread",
        "threadName",
        "exc_info",
        "exc_text",
        "stack_info",
        "taskName",
        "stackLevel",
    }
)

_CONSOLE_LOG_COLORS: dict[str, str] = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


class _UtcTextFormatter(logging.Formatter):
    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class _UtcColoredConsoleFormatter(colorlog.ColoredFormatter):
    """UTC timestamps + level-based colors (stderr, TTY / NO_COLOR aware via colorlog)."""

    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class StructuredJsonFormatter(logging.Formatter):
    """One JSON object per log line for log platforms / jq."""

    def format(self, record: LogRecord) -> str:
        ts = (
            datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        payload: dict[str, Any] = {
            "timestamp": ts,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "src_file": record.filename,
            "src_line": record.lineno,
            "src_func": record.funcName,
        }
        for key, value in record.__dict__.items():
            if key in _JSON_MERGE_SKIP or key.startswith("_"):
                continue
            if value is None:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def _stderr_formatter(settings: Settings) -> logging.Formatter:
    """Console sink: JSON for aggregators, else colored or plain UTC text."""
    if settings.log_console_json:
        return StructuredJsonFormatter()
    fmt = "%(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%SZ"
    if settings.log_color:
        return _UtcColoredConsoleFormatter(
            fmt,
            datefmt=datefmt,
            log_colors=_CONSOLE_LOG_COLORS,
            reset=True,
            stream=sys.stderr,
            no_color=os.environ.get("NO_COLOR", "").strip() != "",
        )
    return _UtcTextFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt=datefmt,
    )


def configure_logging(settings: Settings | None = None) -> None:
    """
    Configure the root logger once (idempotent). Call from ``create_app`` before other setup.

    **Default:** stderr = UTC lines **color-coded by level** (colorlog); rotating ``app.log`` =
    **newline-delimited JSON** when file logging is on (easy to query with jq or a log stack).
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

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(_stderr_formatter(s))

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
            if s.log_file_json:
                file_handler.setFormatter(StructuredJsonFormatter())
            else:
                file_handler.setFormatter(
                    _UtcTextFormatter(
                        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                        datefmt="%Y-%m-%dT%H:%M:%SZ",
                    )
                )
            root.addHandler(file_handler)
        except OSError as exc:
            sys.stderr.write(f"WARNING: could not open log file under {log_dir}: {exc}\n")

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).setLevel(level)

    if level > logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    _configured = True
    logging.getLogger(__name__).debug(
        "Logging configured",
        extra={
            "event": "logging_configured",
            "log_level": level_name,
            "log_file_json": s.log_file_json,
            "log_console_json": s.log_console_json,
            "log_color": s.log_color,
        },
    )


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
