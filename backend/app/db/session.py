"""SQLAlchemy engine and request-scoped sessions.

ARCHITECTURE: Unified database abstraction layer supporting both Postgres and SQLite.
- Automatically detects database type from URL and configures appropriately
- Postgres: uses shared psycopg pool for both SQLAlchemy and LangGraph
- SQLite: uses default pooling, local checkpointer
- No forcing of connection type; app adapts intelligently to the URL
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, StaticPool
from sqlalchemy.orm import Session, sessionmaker

_pool: Any | None = None
_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None
_db_type: str | None = None  # 'postgres' or 'sqlite'


def _detect_db_type(database_url: str | None) -> str | None:
    """Detect database type from URL ('postgres' or 'sqlite', None if not recognized)."""
    if not database_url:
        return None
    if database_url.startswith("postgresql") or database_url.startswith("postgres"):
        return "postgres"
    if database_url.startswith("sqlite"):
        return "sqlite"
    return None


def detect_database_type(database_url: str | None) -> str | None:
    """Public alias for URL-based detection (checkpointer, tools, tests)."""
    return _detect_db_type(database_url)


def _normalize_postgres_conninfo(url: str) -> str:
    """psycopg pool expects a libpq URI, not SQLAlchemy's ``+psycopg`` dialect prefix."""
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url.removeprefix("postgresql+psycopg://")
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + url.removeprefix("postgresql+psycopg2://")
    return url


def normalize_postgres_sqlalchemy_url(url: str) -> str:
    """Force SQLAlchemy to use the psycopg (v3) driver for all supported Postgres URL shapes."""
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql+psycopg2://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    return url


def get_db_type() -> str | None:
    """Return the detected database type ('postgres', 'sqlite', or None)."""
    return _db_type


def configure_pool(database_url: str | None) -> Any:
    """Initialize connection pool (psycopg for Postgres, None for SQLite).
    
    Automatically detects database type from URL and configures appropriately.
    Call this FIRST during app startup, before configure_engine().
    
    Returns the pool (for Postgres) or None (for SQLite).
    """
    global _pool, _db_type
    if _pool is not None:
        return _pool

    db_type = _detect_db_type(database_url)
    _db_type = db_type

    if db_type == "postgres":
        from psycopg_pool import ConnectionPool

        _pool = ConnectionPool(
            conninfo=_normalize_postgres_conninfo(database_url),
            open=True,
            min_size=2,
            max_size=20,
            timeout=30,
            max_idle=300,
        )
        return _pool

    # SQLite or no URL: no pool needed
    return None


def get_pool() -> Any | None:
    """Return the shared psycopg pool (None if SQLite or not initialized)."""
    return _pool


def dispose_pool() -> None:
    """Close the shared connection pool during app shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def configure_engine(database_url: str | None) -> None:
    """Create SQLAlchemy engine, auto-detecting database type from URL.
    
    Postgres: Uses shared psycopg pool (must call configure_pool() first).
    SQLite: Uses StaticPool for local file connections.
    
    Intelligently adapts based on the URL without forcing a single type.
    """
    global _engine, _SessionLocal, _db_type
    dispose_engine()
    if not database_url:
        return

    db_type = _detect_db_type(database_url)
    _db_type = db_type

    if db_type == "postgres":
        # Postgres: use shared pool via creator function
        if _pool is None:
            msg = "Postgres pool not initialized. Call configure_pool() before configure_engine()."
            raise RuntimeError(msg)

        sa_url = normalize_postgres_sqlalchemy_url(database_url)

        def get_connection() -> Any:
            """Creator function: get connection from shared psycopg pool."""
            return _pool.getconn()

        _engine = create_engine(
            sa_url,
            creator=get_connection,
            poolclass=NullPool,  # Use psycopg pool, not SQLAlchemy's QueuePool
        )
    else:
        # SQLite (or other): use SQLAlchemy default pooling
        _engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

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


def database_health() -> tuple[str, str | None]:
    """
    Non-throwing DB probe for ``/health``.

    Returns ``("ok", None)``, ``("not_configured", None)``, or ``("error", message)``.
    """
    if _engine is None:
        return "not_configured", None
    try:
        ping()
    except Exception as exc:  # noqa: BLE001
        return "error", str(exc)[:500]
    return "ok", None


def open_tool_session() -> Session:
    """Return a new ORM session for LangChain tools. Caller must ``close()``.
    
    IMPORTANT: Always wrap in try/finally to ensure proper cleanup:
        session = open_tool_session()
        try:
            # use session
            pass
        finally:
            session.close()
            
    Or prefer session_scope() context manager for new code.
    """
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


@contextmanager
def session_scope() -> Generator[Session, Any, None]:
    """Context manager for safe tool session lifecycle.
    
    Ensures proper connection return to pool even on exceptions.
    Prefer this over open_tool_session() for new code.
    
    Usage:
        with session_scope() as session:
            user = session.get(User, user_id)
    """
    if _SessionLocal is None:
        msg = "Database is not configured. Set DATABASE_URL in the environment."
        raise RuntimeError(msg)
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
