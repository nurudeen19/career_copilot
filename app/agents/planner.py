"""Planner: current state, target role, constraints."""


def run(context: dict) -> dict:
    user_message = context.get("user_message", "")
    return {
        "agent": "planner",
        "current_state": None,
        "target_role": None,
        "constraints": {"time": None, "money": None, "location": None},
        "subtasks": [],
        "notes": "Replace with LLM: parse user_message into structured plan.",
        "raw_user_message": user_message,
    }
