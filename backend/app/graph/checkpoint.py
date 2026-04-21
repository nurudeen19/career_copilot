"""LangGraph checkpointer: Postgres when DATABASE_URL is set, else SQLite file."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.config.settings import Settings, get_settings

_pool: Any | None = None
_sqlite_conn: sqlite3.Connection | None = None
_saver: Any | None = None


def _normalize_postgres_conninfo(url: str) -> str:
    """psycopg pool expects a libpq URI, not SQLAlchemy's ``+psycopg`` dialect prefix."""
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url.removeprefix("postgresql+psycopg://")
    return url


def get_checkpointer(settings: Settings | None = None) -> Any:
    """Return a process-wide checkpointer (creates tables / file on first use)."""
    global _pool, _sqlite_conn, _saver
    if _saver is not None:
        return _saver

    s = settings or get_settings()
    if s.database_url:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg_pool import ConnectionPool

        _pool = ConnectionPool(
            conninfo=_normalize_postgres_conninfo(s.database_url),
            open=True,
            max_size=5,
        )
        _saver = PostgresSaver(_pool)
        _saver.setup()
        return _saver

    from langgraph.checkpoint.sqlite import SqliteSaver

    path = Path(s.workflow.graph_checkpoint_sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _sqlite_conn = sqlite3.connect(str(path), check_same_thread=False)
    _saver = SqliteSaver(_sqlite_conn)
    return _saver


def dispose_checkpointer() -> None:
    """Close pool / sqlite connection when resetting runtime."""
    global _pool, _sqlite_conn, _saver
    if _pool is not None:
        _pool.close()
        _pool = None
    if _sqlite_conn is not None:
        _sqlite_conn.close()
        _sqlite_conn = None
    _saver = None
