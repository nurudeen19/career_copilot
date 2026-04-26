"""SQLAlchemy engine and request-scoped sessions.

ARCHITECTURE: Unified database abstraction layer supporting both Postgres and SQLite.
- Automatically detects database type from URL and configures appropriately
- Postgres: **two** ``psycopg_pool.ConnectionPool`` instances (same server, separate caps):
  one for SQLAlchemy only, one for LangGraph PostgresSaver only. That avoids one subsystem
  exhausting the shared bucket during long multi-minute agentic runs.
- Both pools use ``close_returns=True`` so ``Connection.close()`` returns the client to the pool.
  **Required** for the SQLAlchemy ``NullPool`` + ``getconn()`` integration; otherwise connections
  are not recycled and you eventually hit ``PoolTimeout``.
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

_pool_sa: Any | None = None
_pool_checkpoint: Any | None = None
_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None
_db_type: str | None = None  # 'postgres' or 'sqlite'

# Long agentic workflows: many short checkpoint checkouts + occasional ORM tool sessions.
# Acquire timeout must cover worst-case queueing; max_idle applies only to connections
# sitting **in** the pool (not while checked out for an active graph step).
_POOL_TIMEOUT_S = 180.0
_POOL_SA_MIN = 1
_POOL_SA_MAX = 10
_POOL_CP_MIN = 2
_POOL_CP_MAX = 12
_POOL_MAX_IDLE_S = 30 * 60.0
_POOL_MAX_LIFETIME_S = 2 * 60 * 60.0
_POOL_RECONNECT_TIMEOUT_S = 10 * 60.0


def _pool_check_connection(conn: Any) -> None:
    """Run before handing a pooled connection to a client (stale TCP / server drops)."""
    conn.execute("SELECT 1")


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


def configure_pool(database_url: str | None) -> tuple[Any | None, Any | None]:
    """Initialize psycopg pools for Postgres (SQLAlchemy + checkpoint), or None for SQLite.

    Call this FIRST during app startup, before configure_engine().

    Returns ``(sqlalchemy_pool, checkpoint_pool)`` for Postgres, else ``(None, None)``.
    """
    global _pool_sa, _pool_checkpoint, _db_type
    if _pool_sa is not None:
        return _pool_sa, _pool_checkpoint

    db_type = _detect_db_type(database_url)
    _db_type = db_type

    if db_type == "postgres":
        from psycopg_pool import ConnectionPool

        conninfo = _normalize_postgres_conninfo(database_url)
        pool_kw: dict[str, Any] = {
            "conninfo": conninfo,
            "open": True,
            "timeout": _POOL_TIMEOUT_S,
            "max_idle": _POOL_MAX_IDLE_S,
            "max_lifetime": _POOL_MAX_LIFETIME_S,
            "reconnect_timeout": _POOL_RECONNECT_TIMEOUT_S,
            "check": _pool_check_connection,
            # SQLAlchemy NullPool calls .close() on checkout; without this, conns are not put back
            # in the pool → exhaustion and PoolTimeout after long / concurrent workflows.
            "close_returns": True,
        }
        _pool_sa = ConnectionPool(
            min_size=_POOL_SA_MIN,
            max_size=_POOL_SA_MAX,
            name="sqlalchemy",
            **pool_kw,
        )
        _pool_checkpoint = ConnectionPool(
            min_size=_POOL_CP_MIN,
            max_size=_POOL_CP_MAX,
            name="langgraph_checkpoint",
            **pool_kw,
        )
        return _pool_sa, _pool_checkpoint

    # SQLite or no URL: no pool needed
    return None, None


def get_pool() -> Any | None:
    """Return the LangGraph / checkpoint psycopg pool (None if SQLite or not initialized)."""
    return _pool_checkpoint


def get_sqlalchemy_pool() -> Any | None:
    """Return the ORM-only psycopg pool (None if SQLite or not initialized)."""
    return _pool_sa


def dispose_pool() -> None:
    """Close psycopg pools during app shutdown."""
    global _pool_sa, _pool_checkpoint
    for p in (_pool_sa, _pool_checkpoint):
        if p is not None:
            p.close()
    _pool_sa = None
    _pool_checkpoint = None


def configure_engine(database_url: str | None) -> None:
    """Create SQLAlchemy engine, auto-detecting database type from URL.
    
    Postgres: Uses the ORM-only psycopg pool (must call configure_pool() first).
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
        # Postgres: ORM-only psycopg pool via creator (NullPool = no second SA pool layer).
        if _pool_sa is None:
            msg = "Postgres pool not initialized. Call configure_pool() before configure_engine()."
            raise RuntimeError(msg)

        sa_url = normalize_postgres_sqlalchemy_url(database_url)

        def get_connection() -> Any:
            """Creator: checkout from the SQLAlchemy-dedicated psycopg pool."""
            return _pool_sa.getconn()

        _engine = create_engine(
            sa_url,
            creator=get_connection,
            poolclass=NullPool,
            pool_pre_ping=True,
        )
    else:
        # SQLite (or other): use SQLAlchemy default pooling
        _engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
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
