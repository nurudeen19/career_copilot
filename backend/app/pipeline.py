"""Single-turn pipeline: default agent order for one user message."""

from app.agents.registry import get_agent_bundle
from app.core.agent_runtime import get_agent_runtime


def run_turn(user_message: str) -> dict:
    runtime = get_agent_runtime()
    agents = get_agent_bundle(runtime)
    ctx: dict = {"user_message": user_message}
    ctx["plan"] = agents.planner.run(ctx)
    ctx["research"] = agents.research.run(ctx)
    ctx["analysis"] = agents.analyst.run(ctx)
    ctx["critique"] = agents.critic.run(ctx)
    ctx["synthesis"] = agents.synthesizer.run(ctx)
    return ctx


def apply_feedback(ctx: dict, user_feedback: str) -> dict:
    """Call after a 👎 or follow-up correction; mutates and returns ctx."""
    ctx["user_feedback"] = user_feedback
    runtime = get_agent_runtime()
    agents = get_agent_bundle(runtime)
    ctx["feedback"] = agents.feedback.run(ctx)
    return ctx
