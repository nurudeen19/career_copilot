"""Pytest fixtures: isolated SQLite DB, settings cache reset, TestClient."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.config.settings import get_settings
from app.db.session import configure_engine, dispose_engine, get_engine
from app.models.base import Base


@pytest.fixture(autouse=True)
def _stub_password_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Avoid passlib/bcrypt backend self-tests that fail on some bcrypt 4.x + Python combos.
    Auth flow still exercises DB + JWT; only the digest format is non-production.
    """
    import app.services.auth as auth_mod

    def fake_hash(plain: str) -> str:
        return "test$" + plain

    def fake_verify(plain: str, hashed: str) -> bool:
        return hashed == "test$" + plain

    monkeypatch.setattr(auth_mod, "_hash_password", fake_hash)
    monkeypatch.setattr(auth_mod, "_verify_password", fake_verify)


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    """Ensure ``get_settings()`` picks up monkeypatched env per test."""
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
