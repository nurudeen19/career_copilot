"""One-time app initialization (config load, future: logging, clients)."""

from app.config.settings import get_settings


def init_app() -> None:
    """Load settings."""
    get_settings()
