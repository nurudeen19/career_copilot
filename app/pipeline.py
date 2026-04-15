"""Single-turn pipeline: default agent order for one user message."""

from app.agents import analyze, analyze_feedback, critique, plan, research, synthesize


def run_turn(user_message: str) -> dict:
    ctx: dict = {"user_message": user_message}
    ctx["plan"] = plan(ctx)
    ctx["research"] = research(ctx)
    ctx["analysis"] = analyze(ctx)
    ctx["critique"] = critique(ctx)
    ctx["synthesis"] = synthesize(ctx)
    return ctx


def apply_feedback(ctx: dict, user_feedback: str) -> dict:
    """Call after a 👎 or follow-up correction; mutates and returns ctx."""
    ctx["user_feedback"] = user_feedback
    ctx["feedback"] = analyze_feedback(ctx)
    return ctx
