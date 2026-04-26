"""Bounded chat history for agents that need **conversation** context (planner only).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from langchain_core.messages import AnyMessage, trim_messages

if TYPE_CHECKING:
    from app.config.settings import Settings

_log = logging.getLogger(__name__)

# Hard floor so a tiny misconfiguration does not collapse history to a single turn.
_MIN_HISTORY_TOKENS = 512


def messages_for_llm(messages: Sequence[AnyMessage] | None, settings: Settings) -> list[AnyMessage]:
    """Return a recent window of ``messages`` under ``settings.llm_history_max_tokens`` (approximate)."""
    seq = [m for m in (messages or ()) if m is not None]
    if not seq:
        return []

    cap = int(settings.llm_history_max_tokens)
    cap = max(cap, _MIN_HISTORY_TOKENS)

    try:
        trimmed = trim_messages(
            list(seq),
            max_tokens=cap,
            token_counter="approximate",
            strategy="last",
            start_on="human",
            include_system=True,
        )
    except Exception:
        _log.warning(
            "messages_for_llm: trim_messages failed; using last 24 messages",
            extra={"event": "message_history_trim_failed", "fallback_message_count": 24},
            exc_info=True,
        )
        return list(seq[-24:]) if len(seq) > 24 else list(seq)

    if trimmed:
        return trimmed
    return [seq[-1]]
