"""SQLAlchemy engine lifecycle and ``database_health``."""

from __future__ import annotations

import pytest

from app.config.settings import get_settings
from app.db.session import (
    configure_engine,
    database_health,
    dispose_engine,
    get_engine,
    ping,
)
from app.models.base import Base


def test_database_health_not_configured_after_dispose() -> None:
    dispose_engine()
    assert database_health() == ("not_configured", None)


def test_get_engine_raises_when_unconfigured() -> None:
    dispose_engine()
    with pytest.raises(RuntimeError, match="not configured"):
        get_engine()


def test_ping_after_sqlite_configured(sqlite_database: str) -> None:
    ping()
    assert database_health() == ("ok", None)


def test_configure_engine_replace(sqlite_database: str, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    ping()
    path2 = tmp_path / "second.db"
    url2 = f"sqlite+pysqlite:///{path2}"
    monkeypatch.setenv("DATABASE_URL", url2)
    get_settings.cache_clear()
    configure_engine(url2)
    import app.models.user  # noqa: F401
    import app.models.user_profile  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
    ping()
    assert database_health() == ("ok", None)
