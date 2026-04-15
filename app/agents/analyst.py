"""Analyst: skill gap, feasibility, timeline."""


def run(context: dict) -> dict:
    plan = context.get("plan") or {}
    research = context.get("research") or {}
    return {
        "agent": "analyst",
        "skill_gaps": [],
        "feasibility_score": None,
        "timeline_estimate": None,
        "notes": "Replace with LLM using plan + research artifacts.",
        "inputs_summary": {"plan_keys": list(plan.keys()), "research_keys": list(research.keys())},
    }
