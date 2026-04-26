"""Register and delete workflow checkpoint threads with user ownership checks."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import session_scope
from app.graph.checkpoint import delete_thread_checkpoints, get_checkpointer
from app.models.user import User
from app.models.workflow_thread import WorkflowThread

_log = logging.getLogger(__name__)


def _parse_thread_id(thread_id: str) -> str:
    return str(uuid.UUID(str(thread_id).strip()))


def _normalize_thread_id(thread_id: str) -> str:
    try:
        return _parse_thread_id(thread_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid thread_id") from exc


def _owner_from_checkpoint_tuple(tup: Any) -> str | None:
    if tup is None:
        return None
    ck = getattr(tup, "checkpoint", None) or {}
    if not isinstance(ck, dict):
        return None
    ch = ck.get("channel_values") or {}
    if not isinstance(ch, dict):
        return None
    uid = ch.get("user_id")
    if uid is None:
        return None
    s = str(uid).strip()
    return s or None


def register_workflow_thread(*, user_id: uuid.UUID, thread_id: str) -> None:
    """Record that ``thread_id`` belongs to ``user_id`` (idempotent)."""
    try:
        tid = _parse_thread_id(thread_id)
    except ValueError as exc:
        raise RuntimeError("invalid thread_id for register") from exc
    with session_scope() as db:
        existing = db.scalar(select(WorkflowThread).where(WorkflowThread.thread_id == tid))
        if existing is not None:
            if existing.user_id != user_id:
                _log.error(
                    "Workflow thread_id collision",
                    extra={
                        "event": "workflow_thread_collision",
                        "thread_id": tid,
                        "expected_user_id": str(user_id),
                        "found_user_id": str(existing.user_id),
                    },
                )
                raise RuntimeError("thread_id collision")
            return
        db.add(WorkflowThread(user_id=user_id, thread_id=tid))


def delete_workflow_thread_for_user(db: Session, user: User, thread_id: str) -> None:
    """
    Remove checkpoint data for ``thread_id`` when the current user owns that thread.

    Ownership: ``workflow_threads`` row, else legacy checkpoints whose state ``user_id`` matches.
    """
    tid = _normalize_thread_id(thread_id)

    row = db.scalar(select(WorkflowThread).where(WorkflowThread.thread_id == tid))
    if row is not None:
        if row.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not allowed to delete this thread")
        delete_thread_checkpoints(tid)
        db.delete(row)
        db.commit()
        return

    saver = get_checkpointer()
    tup: Any
    try:
        tup = saver.get_tuple({"configurable": {"thread_id": tid}})
    except Exception:  # noqa: BLE001
        _log.exception(
            "Checkpoint get_tuple failed during thread delete",
            extra={"event": "workflow_thread_delete_get_tuple_failed", "thread_id": tid},
        )
        tup = None

    if tup is None:
        return

    owner = _owner_from_checkpoint_tuple(tup)
    if owner != str(user.id):
        raise HTTPException(status_code=403, detail="Not allowed to delete this thread")

    delete_thread_checkpoints(tid)
