"""SQLAlchemy engine and request-scoped sessions."""

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def configure_engine(database_url: str | None) -> None:
    """Create (or replace) the global engine from settings."""
    global _engine, _SessionLocal
    dispose_engine()
    if not database_url:
        return
    _engine = create_engine(database_url, pool_pre_ping=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_engine() -> Engine:
    if _engine is None:
        msg = "Database is not configured. Set DATABASE_URL in the environment."
        raise RuntimeError(msg)
    return _engine


def dispose_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def ping() -> None:
    """Run a trivial query to verify connectivity."""
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))


def open_tool_session() -> Session:
    """Return a new ORM session for LangChain tools. Caller must ``close()``."""
    if _SessionLocal is None:
        msg = "Database is not configured. Set DATABASE_URL in the environment."
        raise RuntimeError(msg)
    return _SessionLocal()


def get_db() -> Generator[Session, Any, None]:
    if _SessionLocal is None:
        msg = "Database is not configured. Set DATABASE_URL in the environment."
        raise RuntimeError(msg)
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
