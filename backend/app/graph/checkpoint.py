"""LangGraph checkpointer: auto-detects Postgres or SQLite.

ARCHITECTURE: Gets the shared connection pool from app.db.session.
- The pool is initialized and managed by session.py (single source of truth for DB)
- This module auto-detects DB type and uses appropriate checkpointer
- Intelligently adapts without forcing a single type
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.config.settings import Settings, get_settings
from app.db.session import detect_database_type, get_pool

_sqlite_conn: sqlite3.Connection | None = None
_saver: Any | None = None


def _patch_langgraph_postgres_index_migrations() -> None:
    """LangGraph uses ``CREATE INDEX CONCURRENTLY``; psycopg runs ``setup()`` in a transaction, which Postgres rejects."""
    from langgraph.checkpoint.postgres import base as lg_pg_base

    migs = lg_pg_base.MIGRATIONS
    for i, sql in enumerate(migs):
        if isinstance(sql, str) and "CONCURRENTLY" in sql:
            migs[i] = sql.replace("CREATE INDEX CONCURRENTLY", "CREATE INDEX")


def get_checkpointer(settings: Settings | None = None) -> Any:
    """Return the process-wide checkpointer, auto-detecting database type.

    Postgres: Uses the shared pool from app.db.session.get_pool().
    SQLite: Creates a local file connection.
    
    Intelligently adapts based on DATABASE_URL without forcing a single type.
    """
    global _sqlite_conn, _saver
    if _saver is not None:
        return _saver

    s = settings or get_settings()
    db_type = detect_database_type(s.database_url)

    if db_type == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver

        _patch_langgraph_postgres_index_migrations()
        # Get the shared pool from session module
        pool = get_pool()
        if pool is None:
            msg = "Postgres pool not initialized. Call session.configure_pool() during app startup."
            raise RuntimeError(msg)
        _saver = PostgresSaver(pool)
        _saver.setup()
        return _saver

    # SQLite or no URL: use local file checkpoint
    from langgraph.checkpoint.sqlite import SqliteSaver

    path = Path(s.workflow.graph_checkpoint_sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _sqlite_conn = sqlite3.connect(str(path), check_same_thread=False)
    _saver = SqliteSaver(_sqlite_conn)
    return _saver


def delete_thread_checkpoints(thread_id: str, settings: Settings | None = None) -> None:
    """Remove all LangGraph checkpoints for ``thread_id`` (Postgres or SQLite saver)."""
    saver = get_checkpointer(settings)
    saver.delete_thread(thread_id)


def dispose_checkpointer() -> None:
    """Close checkpointer and SQLite connection only (pool is managed by session module)."""
    global _sqlite_conn, _saver
    if _sqlite_conn is not None:
        _sqlite_conn.close()
        _sqlite_conn = None
    _saver = None
