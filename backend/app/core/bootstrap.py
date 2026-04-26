"""One-time app initialization (config load, database engine)."""

from __future__ import annotations

import logging
from typing import Any

from app.config.settings import get_settings
from app.core.logging_config import configure_logging
from app.db.session import configure_engine, configure_pool, dispose_engine, dispose_pool, ping
from app.graph.checkpoint import dispose_checkpointer, get_checkpointer
from app.guardrails import setup_guardrails, teardown_guardrails

_log = logging.getLogger(__name__)


def _configure_langsmith() -> None:
    """Wire LangSmith from merged :class:`~app.config.settings.Settings` (``Client`` + ``configure``)."""
    try:
        from langsmith import Client, configure as langsmith_configure
    except ImportError:
        _log.warning(
            "LangSmith client not installed; skipping configuration",
            extra={"event": "bootstrap_langsmith_skip", "reason": "import_error"},
        )
        return

    settings = get_settings()
    tracing = bool(settings.langsmith_tracing_enabled)
    key = (settings.langsmith_api_key or "").strip() or None
    api_url = (settings.langsmith_api_url or "").strip() or None

    if tracing and not key:
        _log.warning(
            "LangSmith tracing enabled in settings but API key is empty; tracing disabled",
            extra={
                "event": "bootstrap_langsmith_key_missing",
                "tracing_requested": True,
            },
        )
        tracing = False

    if tracing and key:
        client_kw: dict[str, Any] = {"api_key": key}
        if api_url:
            client_kw["api_url"] = api_url
        client = Client(**client_kw)
        langsmith_configure(
            client=client,
            enabled=True,
            project_name=settings.langsmith_project,
        )
        _log.info(
            "LangSmith tracing enabled",
            extra={
                "event": "bootstrap_langsmith_enabled",
                "langsmith_project": settings.langsmith_project,
            },
        )
    else:
        langsmith_configure(enabled=False, client=None)
        if key and not bool(settings.langsmith_tracing_enabled):
            _log.info(
                "LangSmith API key set but tracing disabled in settings",
                extra={"event": "bootstrap_langsmith_tracing_off", "has_api_key": True},
            )
        else:
            _log.info(
                "LangSmith tracing disabled",
                extra={"event": "bootstrap_langsmith_disabled"},
            )


def init_app() -> None:
    """Load settings, LangSmith client, shared DB pool, SQLAlchemy engine, guardrails, and checkpointer (one-time)."""
    settings = get_settings()
    configure_logging(settings)
    _log.info(
        "Bootstrap: LangSmith",
        extra={"event": "bootstrap_init_step", "step": "langsmith"},
    )
    _configure_langsmith()
    _log.info(
        "Bootstrap: connection pools",
        extra={"event": "bootstrap_init_step", "step": "configure_pool"},
    )
    configure_pool(settings.database_url)
    _log.info(
        "Bootstrap: SQLAlchemy engine",
        extra={"event": "bootstrap_init_step", "step": "configure_engine"},
    )
    configure_engine(settings.database_url)
    _log.info(
        "Bootstrap: prompt guard",
        extra={
            "event": "bootstrap_init_step",
            "step": "setup_guardrails",
            "prompt_guard_model_id": settings.prompt_guard.model_id,
        },
    )
    setup_guardrails(settings)
    _log.info(
        "Bootstrap: LangGraph checkpointer",
        extra={"event": "bootstrap_init_step", "step": "get_checkpointer"},
    )
    get_checkpointer(settings)
    _log.info("Bootstrap complete", extra={"event": "bootstrap_init_complete"})


def verify_database_connection() -> None:
    """Fail fast if the database URL is set but the server is unreachable."""
    settings = get_settings()
    if not settings.database_url:
        return
    _log.info("Database ping", extra={"event": "database_verify_start"})
    ping()
    _log.info("Database ping ok", extra={"event": "database_verify_ok"})


def shutdown_app() -> None:
    """Release database connections, checkpoint pool, guardrails, and flush LangSmith."""
    _log.info("Shutdown: guardrails", extra={"event": "shutdown_step", "step": "teardown_guardrails"})
    teardown_guardrails()
    _log.info("Shutdown: checkpointer", extra={"event": "shutdown_step", "step": "dispose_checkpointer"})
    dispose_checkpointer()
    _log.info("Shutdown: SQLAlchemy engine", extra={"event": "shutdown_step", "step": "dispose_engine"})
    dispose_engine()
    _log.info("Shutdown: connection pools", extra={"event": "shutdown_step", "step": "dispose_pool"})
    dispose_pool()
    try:
        from langchain_core.tracers.langchain import wait_for_all_tracers

        wait_for_all_tracers()
    except Exception:  # noqa: BLE001
        _log.debug(
            "wait_for_all_tracers skipped or failed during shutdown",
            extra={"event": "shutdown_langsmith_tracers"},
            exc_info=True,
        )
    try:
        from langsmith import configure as langsmith_configure

        langsmith_configure(enabled=False, client=None)
    except ImportError:
        pass
    _log.info("Shutdown complete", extra={"event": "shutdown_complete"})
