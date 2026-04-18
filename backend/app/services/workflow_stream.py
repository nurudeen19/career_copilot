"""Stream LangGraph workflow updates; retries only before any chunk is emitted (transient errors)."""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, message_to_dict

from app.core.agent_runtime import AgentRuntime, get_agent_runtime
from app.core.retry_policy import is_transient_workflow_error
from app.graph.career_graph import stream_graph_updates
from app.models.user import User
from app.schema.workflow import WorkflowStreamRequest

_log = logging.getLogger("app.workflow")

_QUEUE_END: Any = object()


def _serialize_value(obj: Any) -> Any:
    if isinstance(obj, BaseMessage):
        return message_to_dict(obj)
    if isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_value(v) for v in obj]
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:  # noqa: BLE001
            pass
    return obj


def build_workflow_initial_state(body: WorkflowStreamRequest, user: User) -> dict[str, Any]:
    """Map the HTTP body to graph ``invoke`` input (guardrails still run inside the graph)."""
    initial: dict[str, Any] = {"user_id": str(user.id)}
    msg = (body.message or "").strip()
    fb = (body.user_feedback or "").strip()
    if fb:
        initial["user_feedback"] = fb
    if msg:
        initial["messages"] = [HumanMessage(content=msg)]
    return initial


def _sse_line(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"


def iter_workflow_sse(
    body: WorkflowStreamRequest,
    user: User,
    *,
    runtime: AgentRuntime | None = None,
    max_stream_attempts: int = 3,
) -> Iterator[str]:
    """
    Yield ``text/event-stream`` frames (sync). Each ``data:`` JSON has ``thread_id``, ``step``, ``patch``.
    Final frame: ``{"event": "done", "thread_id": ...}``; errors: ``{"event": "error", "detail": ...}``.
    """
    rt = runtime or get_agent_runtime()
    tid = str(body.thread_id) if body.thread_id else str(uuid.uuid4())
    initial = build_workflow_initial_state(body, user)

    attempt = 0
    while attempt < max_stream_attempts:
        emitted = False
        try:
            for update in stream_graph_updates(initial, thread_id=tid, runtime=rt):
                emitted = True
                if not isinstance(update, dict):
                    yield _sse_line({"thread_id": tid, "step": "_", "patch": _serialize_value(update)})
                    continue
                for step, patch in update.items():
                    yield _sse_line(
                        {
                            "thread_id": tid,
                            "step": step,
                            "patch": _serialize_value(patch),
                        }
                    )
            yield _sse_line({"event": "done", "thread_id": tid})
            return
        except Exception as exc:  # noqa: BLE001
            if emitted or not is_transient_workflow_error(exc):
                yield _sse_line({"event": "error", "thread_id": tid, "detail": str(exc)})
                return
            attempt += 1
            if attempt >= max_stream_attempts:
                yield _sse_line({"event": "error", "thread_id": tid, "detail": str(exc)})
                return
            time.sleep(min(8.0, 0.5 * (2 ** (attempt - 1))))


def _sse_producer(
    q: queue.Queue[Any],
    body: WorkflowStreamRequest,
    user: User,
    runtime: AgentRuntime | None,
    max_stream_attempts: int,
) -> None:
    try:
        for line in iter_workflow_sse(body, user, runtime=runtime, max_stream_attempts=max_stream_attempts):
            q.put(line)
    except Exception as exc:  # noqa: BLE001
        q.put(exc)
    finally:
        q.put(_QUEUE_END)


async def aiter_workflow_sse(
    body: WorkflowStreamRequest,
    user: User,
    *,
    runtime: AgentRuntime | None = None,
    max_stream_attempts: int = 3,
) -> AsyncIterator[bytes]:
    """
    Async SSE: one background thread runs the sync LangGraph stream so ``ContextVar`` workflow
    user binding stays consistent, while the event loop awaits queue gets without blocking between chunks.
    """
    tid = str(body.thread_id) if body.thread_id else str(uuid.uuid4())
    _log.info("workflow_stream_start user_id=%s thread_id=%s", user.id, tid)
    q: queue.Queue[Any] = queue.Queue()
    worker = threading.Thread(
        target=_sse_producer,
        args=(q, body, user, runtime, max_stream_attempts),
        name="workflow-sse",
        daemon=True,
    )
    worker.start()
    try:
        while True:
            item = await asyncio.to_thread(q.get)
            if item is _QUEUE_END:
                break
            if isinstance(item, BaseException):
                _log.exception("workflow_stream_error user_id=%s thread_id=%s", user.id, tid)
                raise item
            yield str(item).encode("utf-8")
    finally:
        worker.join(timeout=0.5)
        if worker.is_alive():
            _log.warning(
                "workflow_stream thread still running after disconnect or timeout user_id=%s thread_id=%s",
                user.id,
                tid,
            )

