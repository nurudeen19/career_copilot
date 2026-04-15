"""Critic: challenge timelines, constraints, assumptions."""


def run(context: dict) -> dict:
    analysis = context.get("analysis") or {}
    return {
        "agent": "critic",
        "concerns": [],
        "missing_constraints": [],
        "risky_assumptions": [],
        "notes": "Replace with LLM: stress-test analysis + plan.",
        "analysis_keys": list(analysis.keys()),
    }
