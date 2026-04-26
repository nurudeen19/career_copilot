"""Input guardrails: size limits + HF prompt guard. Wired at startup; graph only invokes checks."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from app.config.settings import Settings, get_settings
from app.guardrails.input_size import validate_input_size
from app.guardrails.prompt_guard import classify_prompt, setup_prompt_guard, teardown_prompt_guard

_log = logging.getLogger(__name__)


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
    """Graph step 0: size then prompt guard. Returns ``{validation_error: str}`` (empty string if ok).

    Logs every decision at INFO/WARNING (no raw user text). A *pass* from Llama Prompt Guard 2 only
    means the classifier scored the text as benign — it can still miss subtle or novel injections
    (downstream planner/system prompts remain important).
    """
    s = settings or get_settings()
    text = _user_text_from_state(state)
    if not text:
        _log.warning(
            "Input guardrails rejected empty text",
            extra={"event": "input_guardrails_empty"},
        )
        return {"validation_error": "No message to process."}

    source = "user_feedback" if (state.get("user_feedback") or "").strip() else "user_message"
    n_chars = len(text)

    size_err = validate_input_size(text, s)
    if size_err:
        _log.warning(
            "Input guardrails rejected message (size)",
            extra={
                "event": "input_guardrails_size_reject",
                "source": source,
                "char_count": n_chars,
                "detail": (size_err[:200] + "…") if len(size_err) > 200 else size_err,
            },
        )
        return {"validation_error": size_err}

    safe, denial = classify_prompt(text, settings=s)
    if safe:
        _log.info(
            "Input guardrails passed",
            extra={
                "event": "input_guardrails_passed",
                "source": source,
                "char_count": n_chars,
            },
        )
        return {"validation_error": ""}

    _log.warning(
        "Input guardrails rejected message (prompt guard)",
        extra={
            "event": "input_guardrails_prompt_reject",
            "source": source,
            "char_count": n_chars,
            "detail": (denial or "blocked")[:160],
        },
    )
    return {"validation_error": denial or "This message could not be accepted."}
