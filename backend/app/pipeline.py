"""CLI-oriented wrappers around the career graph (HTTP API uses ``/workflow/stream``)."""

from __future__ import annotations

import json
import uuid

from langchain_core.messages import HumanMessage, SystemMessage

from app.config.settings import get_settings
from app.core.bootstrap import init_app
from app.graph import build_graph, run_graph
from app.graph.career_graph_runner import invoke_career_graph


def run_turn(user_message: str, user_id: str | None = None, thread_id: str | None = None) -> dict:
    """First message (or new conversation): supplies ``thread_id`` to enable checkpoint memory."""
    init_app()
    tid = thread_id or str(uuid.uuid4())
    out = run_graph(user_message, thread_id=tid, user_id=user_id)
    out["thread_id"] = tid
    return out


def apply_feedback(ctx: dict, user_feedback: str) -> dict:
    """Re-enter after dissatisfaction; requires ``ctx['thread_id']`` from a prior ``run_turn``."""
    init_app()
    tid = ctx.get("thread_id") or str(uuid.uuid4())
    wf = build_graph()
    msgs: list = [HumanMessage(content=ctx.get("user_message") or "")]
    if ctx.get("synthesis"):
        msgs.append(
            SystemMessage(
                content="Previous assistant synthesis (context):\n"
                + json.dumps(ctx["synthesis"], default=str)[:8000]
            )
        )
    final = invoke_career_graph(
        wf,
        {
            "messages": msgs,
            "user_id": ctx.get("user_id"),
            "user_feedback": user_feedback,
            "plan": ctx.get("plan") or {},
        },
        {"configurable": {"thread_id": tid}},
        settings=get_settings(),
    )
    ctx.update(
        {
            "thread_id": tid,
            "messages": final.get("messages"),
            "plan": final.get("plan"),
            "research": final.get("research"),
            "analysis": final.get("analysis"),
            "critique": final.get("critique"),
            "synthesis": final.get("synthesis"),
        }
    )
    return ctx
