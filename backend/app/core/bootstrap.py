"""One-time app initialization (config load, database engine)."""

import logging
import os

from app.config.settings import get_settings
from app.core.logging_config import configure_logging
from app.db.session import configure_engine, dispose_engine, ping
from app.guardrails import setup_guardrails, teardown_guardrails

_log = logging.getLogger(__name__)


def _configure_langsmith_tracing() -> None:
    """Configure LangSmith / LangChain client env (tracing flag + project + API key)."""
    settings = get_settings()
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    if settings.langchain_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    if settings.langchain_tracing_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"


def init_app() -> None:
    """Load settings, tracing env, DB engine, and prompt-guard model (one-time, avoids first-request latency)."""
    settings = get_settings()
    configure_logging(settings)
    _log.info("init_app: configuring LangSmith / LangChain tracing env")
    _configure_langsmith_tracing()
    _log.info("init_app: configuring SQLAlchemy engine")
    configure_engine(settings.database_url)
    _log.info("init_app: loading prompt guard (%s)", settings.prompt_guard_model_id)
    setup_guardrails(settings)
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
    """Release database connections and unload guardrail models."""
    _log.info("shutdown_app: unloading guardrails")
    teardown_guardrails()
    _log.info("shutdown_app: disposing database engine")
    dispose_engine()
