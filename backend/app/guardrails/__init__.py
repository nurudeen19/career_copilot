"""Input guardrails: size limits + HF prompt guard. Wired at startup; graph only invokes checks."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from app.config.settings import Settings, get_settings
from app.graph.feedback_markers import THUMBS_DOWN_FEEDBACK_MARK
from app.guardrails.input_size import validate_input_size
from app.guardrails.prompt_guard import classify_prompt, setup_prompt_guard, teardown_prompt_guard

_log = logging.getLogger(__name__)


def setup_guardrails(settings: Settings | None = None) -> None:
    """Load prompt guard weights during app bootstrap (avoids first-request latency)."""
    setup_prompt_guard(settings or get_settings())


def teardown_guardrails() -> None:
    """Release prompt guard model (e.g. on shutdown)."""
    teardown_prompt_guard()


def _iter_guard_segments(state: dict) -> list[tuple[str, str]]:
    """(channel, text) pairs to validate. ``user_message`` = latest HumanMessage; ``user_feedback`` optional."""
    out: list[tuple[str, str]] = []
    for m in reversed(state.get("messages") or []):
        if isinstance(m, HumanMessage):
            t = str(m.content or "").strip()
            if t:
                out.append(("user_message", t))
            break
    fb = (state.get("user_feedback") or "").strip()
    if fb:
        out.append(("user_feedback", fb))
    return out


def _should_classify_feedback_segment(text: str, settings: Settings) -> bool:
    """HF prompt guard is a poor fit for correction / rating channels unless explicitly enabled."""
    if text == THUMBS_DOWN_FEEDBACK_MARK:
        return False
    return bool(settings.prompt_guard.classify_user_feedback)


def run_user_input_guardrails(state: dict, settings: Settings | None = None) -> dict:
    """Graph step 0: size on each segment; HF prompt guard on chat only (not ``user_feedback`` by default).

    ``user_feedback`` (thumbs-down marker, free-text corrections) is still length-limited but not scored
    as jailbreak by default — those strings often trip Llama Prompt Guard 2 as false positives.
    Set ``PROMPT_GUARD_CLASSIFY_USER_FEEDBACK=true`` to scan feedback like normal chat.
    """
    s = settings or get_settings()
    segments = _iter_guard_segments(state)
    if not segments:
        _log.warning(
            "Input guardrails rejected empty text",
            extra={"event": "input_guardrails_empty"},
        )
        return {"validation_error": "No message to process."}

    for channel, text in segments:
        source = channel
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

        if channel == "user_feedback" and not _should_classify_feedback_segment(text, s):
            _log.info(
                "Input guardrails skipped HF classifier for user_feedback",
                extra={
                    "event": "input_guardrails_feedback_skip_classifier",
                    "char_count": n_chars,
                    "opaque_marker": text == THUMBS_DOWN_FEEDBACK_MARK,
                },
            )
            continue

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
            continue

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

    return {"validation_error": ""}
