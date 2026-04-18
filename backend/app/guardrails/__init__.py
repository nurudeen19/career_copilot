"""Input guardrails: size limits + HF prompt guard. Wired at startup; graph only invokes checks."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.config.settings import Settings, get_settings
from app.guardrails.input_size import validate_input_size
from app.guardrails.prompt_guard import classify_prompt, setup_prompt_guard, teardown_prompt_guard


def setup_guardrails(settings: Settings | None = None) -> None:
    """Load prompt guard weights during app bootstrap (avoids first-request latency)."""
    setup_prompt_guard(settings or get_settings())


def teardown_guardrails() -> None:
    """Release prompt guard model (e.g. on shutdown)."""
    teardown_prompt_guard()


def _user_text_from_state(state: dict) -> str:
    fb = (state.get("user_feedback") or "").strip()
    if fb:
        return fb
    for m in reversed(state.get("messages") or []):
        if isinstance(m, HumanMessage):
            return str(m.content or "").strip()
    return ""


def run_user_input_guardrails(state: dict, settings: Settings | None = None) -> dict:
    """Graph step 0: size then prompt guard. Returns ``{validation_error: str}`` (empty string if ok)."""
    s = settings or get_settings()
    text = _user_text_from_state(state)
    if not text:
        return {"validation_error": "No message to process."}

    size_err = validate_input_size(text, s)
    if size_err:
        return {"validation_error": size_err}

    safe, denial = classify_prompt(text)
    if safe:
        return {"validation_error": ""}
    return {"validation_error": denial or "This message could not be accepted."}
