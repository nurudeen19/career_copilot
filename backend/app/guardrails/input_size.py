"""Hard limits on user text length before any model work."""

from __future__ import annotations

from app.config.settings import Settings


def validate_input_size(text: str, settings: Settings) -> str | None:
    """Return a user-facing error string, or ``None`` if within limits."""
    if len(text) > settings.workflow.max_user_input_chars:
        return (
            f"Message is too long ({len(text)} characters). "
            f"Please shorten to under {settings.workflow.max_user_input_chars} characters and try again."
        )
    est_tokens = max(len(text) // 4, 1)
    if est_tokens > settings.workflow.max_user_estimated_tokens:
        return (
            "Message appears to exceed safe token limits for this service. "
            "Please shorten your question and try again."
        )
    return None
