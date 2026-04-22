"""Conversation window passed to agents (trimmed from checkpointed messages)."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.config.settings import Settings
from app.graph.message_history import messages_for_llm


def test_messages_for_llm_empty() -> None:
    s = Settings(jwt_secret="x" * 12, llm_history_max_tokens=8000)
    assert messages_for_llm(None, s) == []
    assert messages_for_llm([], s) == []


def test_messages_for_llm_keeps_short_history() -> None:
    s = Settings(jwt_secret="x" * 12, llm_history_max_tokens=50_000)
    msgs = [HumanMessage("one"), AIMessage("two"), HumanMessage("three")]
    out = messages_for_llm(msgs, s)
    assert len(out) == 3


def test_messages_for_llm_trims_long_history() -> None:
    s = Settings(jwt_secret="x" * 12, llm_history_max_tokens=512)
    chunk = "word " * 80
    msgs = [HumanMessage("start " + chunk)] + [AIMessage("reply " + chunk) for i in range(12)] + [HumanMessage("end " + chunk)]
    out = messages_for_llm(msgs, s)
    assert len(out) < len(msgs)
    assert out[-1].type == "human"
