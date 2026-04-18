"""One-time app initialization (config load, database engine)."""

import os

from app.config.settings import get_settings
from app.db.session import configure_engine, dispose_engine, ping
from app.guardrails import setup_guardrails, teardown_guardrails


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
    _configure_langsmith_tracing()
    configure_engine(settings.database_url)
    setup_guardrails(settings)


def verify_database_connection() -> None:
    """Fail fast if the database URL is set but the server is unreachable."""
    settings = get_settings()
    if not settings.database_url:
        return
    ping()


def shutdown_app() -> None:
    """Release database connections and unload guardrail models."""
    teardown_guardrails()
    dispose_engine()
