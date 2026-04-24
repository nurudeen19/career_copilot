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
        _log.warning("langsmith not installed; skipping LangSmith configuration")
        return

    settings = get_settings()
    tracing = bool(settings.langsmith_tracing_enabled)
    key = (settings.langsmith_api_key or "").strip() or None
    api_url = (settings.langsmith_api_url or "").strip() or None

    if tracing and not key:
        _log.warning(
            "LangSmith tracing is on (LANGSMITH_TRACING_V2 / LANGSMITH_TRACING_ENABLED) but LANGSMITH_API_KEY "
            "is empty — tracing disabled until a key is set."
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
        _log.info("LangSmith tracing enabled (project=%r)", settings.langsmith_project)
    else:
        langsmith_configure(enabled=False, client=None)
        if key and not bool(settings.langsmith_tracing_enabled):
            _log.info(
                "LangSmith API key is set but tracing is off — set LANGSMITH_TRACING_V2=true "
                "or LANGSMITH_TRACING_ENABLED=true to record runs to LangSmith."
            )
        else:
            _log.info("LangSmith tracing disabled.")


def init_app() -> None:
    """Load settings, LangSmith client, shared DB pool, SQLAlchemy engine, guardrails, and checkpointer (one-time)."""
    settings = get_settings()
    configure_logging(settings)
    _log.info("init_app: configuring LangSmith from settings")
    _configure_langsmith()
    _log.info("init_app: initializing shared connection pool")
    configure_pool(settings.database_url)
    _log.info("init_app: configuring SQLAlchemy engine (using shared pool)")
    configure_engine(settings.database_url)
    _log.info("init_app: loading prompt guard (%s)", settings.prompt_guard.model_id)
    setup_guardrails(settings)
    _log.info("init_app: LangGraph checkpointer (using shared pool)")
    get_checkpointer(settings)
    _log.info("init_app: finished")


def verify_database_connection() -> None:
    """Fail fast if the database URL is set but the server is unreachable."""
    settings = get_settings()
    if not settings.database_url:
        return
    _log.info("verify_database_connection: pinging database")
    ping()
    _log.info("verify_database_connection: ok")


def shutdown_app() -> None:
    """Release database connections, checkpoint pool, guardrails, and flush LangSmith."""
    _log.info("shutdown_app: unloading guardrails")
    teardown_guardrails()
    _log.info("shutdown_app: disposing LangGraph checkpointer")
    dispose_checkpointer()
    _log.info("shutdown_app: disposing database engine (release pool checkouts)")
    dispose_engine()
    _log.info("shutdown_app: disposing shared connection pool")
    dispose_pool()
    try:
        from langchain_core.tracers.langchain import wait_for_all_tracers

        wait_for_all_tracers()
    except Exception:  # noqa: BLE001
        _log.debug("wait_for_all_tracers skipped or failed during shutdown", exc_info=True)
    try:
        from langsmith import configure as langsmith_configure

        langsmith_configure(enabled=False, client=None)
    except ImportError:
        pass
    _log.info("shutdown_app: complete")
