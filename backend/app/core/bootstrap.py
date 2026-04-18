"""One-time app initialization (config load, database engine)."""

import os

from app.config.settings import get_settings
from app.db.session import configure_engine, dispose_engine, ping


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
    """Load settings, tracing env, and configure the database engine when a URL is set."""
    settings = get_settings()
    _configure_langsmith_tracing()
    configure_engine(settings.database_url)


def verify_database_connection() -> None:
    """Fail fast if the database URL is set but the server is unreachable."""
    settings = get_settings()
    if not settings.database_url:
        return
    ping()


def shutdown_app() -> None:
    """Release database connections."""
    dispose_engine()
