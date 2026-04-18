"""Stream LangGraph workflow updates; retries only before any chunk is emitted (transient errors)."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, message_to_dict

from app.core.agent_runtime import AgentRuntime, get_agent_runtime
from app.core.retry_policy import is_transient_workflow_error
from app.graph.career_graph import stream_graph_updates
from app.models.user import User
from app.schema.workflow import WorkflowStreamRequest


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
    Yield ``text/event-stream`` frames. Each ``data:`` JSON has ``thread_id``, ``step`` (node name), ``patch``.
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
