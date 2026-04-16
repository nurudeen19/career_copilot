"""Feedback analyzer: thumbs-down and follow-ups → adaptation hints."""


def run(context: dict) -> dict:
    feedback = context.get("user_feedback")
    return {
        "agent": "feedback",
        "sentiment": "negative" if feedback == "down" else "unknown",
        "adaptation_hints": [],
        "notes": "Replace with LLM or rules when user signals dissatisfaction.",
    }
