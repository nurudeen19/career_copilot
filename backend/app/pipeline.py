"""Career workflow: LangGraph orchestration over specialist agents."""

import json

from app.core.bootstrap import init_app
from app.graph.career_workflow import get_career_workflow, run_career_workflow
from langchain_core.messages import HumanMessage, SystemMessage


def run_turn(user_message: str, user_id: str | None = None) -> dict:
    """Run one user message through validate → planner → … → synthesizer (or early user handoff)."""
    init_app()
    return run_career_workflow(user_message, user_id=user_id)


def apply_feedback(ctx: dict, user_feedback: str) -> dict:
    """Re-enter the graph after dissatisfaction: feedback → planner → …"""
    init_app()
    wf = get_career_workflow()
    msgs: list = [HumanMessage(content=ctx.get("user_message") or "")]
    if ctx.get("synthesis"):
        msgs.append(
            SystemMessage(
                content="Previous assistant synthesis (context):\n"
                + json.dumps(ctx["synthesis"], default=str)[:8000]
            )
        )
    final = wf.invoke(
        {
            "messages": msgs,
            "user_id": ctx.get("user_id"),
            "user_feedback": user_feedback,
            "plan": ctx.get("plan") or {},
        }
    )
    ctx.update(
        {
            "messages": final.get("messages"),
            "plan": final.get("plan"),
            "research": final.get("research"),
            "analysis": final.get("analysis"),
            "critique": final.get("critique"),
            "synthesis": final.get("synthesis"),
            "feedback": final.get("feedback"),
        }
    )
    return ctx
