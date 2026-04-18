"""One-time app initialization (config load, database engine)."""

from app.config.settings import get_settings
from app.db.session import configure_engine, dispose_engine, ping


def init_app() -> None:
    """Load settings and configure the database engine when a URL is set."""
    settings = get_settings()
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
