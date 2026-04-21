"""Pytest fixtures: isolated SQLite DB, settings cache reset, TestClient."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.config.settings import get_settings
from app.db.session import configure_engine, dispose_engine, get_engine
from app.models.base import Base


@pytest.fixture(autouse=True)
def _stub_password_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deterministic password digests for tests (no passlib / Argon2 work)."""
    import app.services.auth as auth_mod

    def fake_hash(plain: str) -> str:
        return "test$" + plain

    def fake_verify_update(plain: str, hashed: str) -> tuple[bool, str | None]:
        ok = hashed == "test$" + plain
        return ok, None

    monkeypatch.setattr(auth_mod, "_hash_password", fake_hash)
    monkeypatch.setattr(auth_mod, "_verify_password_update", fake_verify_update)


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ``get_settings()`` picks up monkeypatched env per test; avoid writing logs under backend/logs."""
    monkeypatch.setenv("LOG_FILE_ENABLED", "0")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _dispose_engine_after_test() -> None:
    yield
    dispose_engine()


@pytest.fixture
def sqlite_database(monkeypatch: pytest.MonkeyPatch, tmp_path) -> str:
    """
    Configure global SQLAlchemy engine to a file-backed SQLite DB and create tables.
    Returns the database URL string.
    """
    db_path = tmp_path / "career_test.db"
    url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("JWT_SECRET", "pytest-jwt-secret-at-least-eight-chars")
    monkeypatch.setenv("AUTH_DEV_AUTO_VERIFY_EMAIL", "true")
    monkeypatch.setenv("RATE_LIMITS__ENABLED", "false")
    get_settings.cache_clear()
    configure_engine(url)
    # Import models so tables register on Base.metadata
    import app.models.user  # noqa: F401
    import app.models.user_profile  # noqa: F401

    Base.metadata.create_all(bind=get_engine())
    return url


@pytest.fixture
def app(sqlite_database: str):  # noqa: ARG001
    from tests.app_factory import create_test_app

    return create_test_app()


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
