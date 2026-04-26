"""Guardrails: user_feedback must not be blocked by HF prompt guard by default."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from app.config.settings import Settings
from app.graph.feedback_markers import THUMBS_DOWN_FEEDBACK_MARK
from app.guardrails import run_user_input_guardrails


@pytest.fixture
def settings_no_guard(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Settings with HF token unset so classify_prompt short-circuits if accidentally called."""
    monkeypatch.setenv("HF_TOKEN", "")
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "")
    monkeypatch.setenv("HUGGINGFACE_TOKEN", "")
    return Settings(jwt_secret="adequate-secret-here", database_url=None)


def test_feedback_only_skips_classifier_when_pipeline_missing(settings_no_guard: Settings) -> None:
    state = {
        "messages": [],
        "user_feedback": "This answer was wrong about salary bands — please redo with sources.",
    }
    out = run_user_input_guardrails(state, settings_no_guard)
    assert out["validation_error"] == ""


def test_thumbs_marker_never_hits_classifier(settings_no_guard: Settings) -> None:
    state = {"messages": [], "user_feedback": THUMBS_DOWN_FEEDBACK_MARK}
    out = run_user_input_guardrails(state, settings_no_guard)
    assert out["validation_error"] == ""


def test_user_message_still_validated(settings_no_guard: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []

    def fake_classify(text: str, settings=None, *, malicious_threshold=None):  # noqa: ANN001
        called.append(text)
        return True, None

    monkeypatch.setattr("app.guardrails.classify_prompt", fake_classify)
    state = {
        "messages": [HumanMessage(content="What is a staff engineer path?")],
    }
    out = run_user_input_guardrails(state, settings_no_guard)
    assert out["validation_error"] == ""
    assert called == ["What is a staff engineer path?"]


def test_both_message_and_feedback_classifies_message_only(
    settings_no_guard: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[str] = []

    def fake_classify(text: str, settings=None, *, malicious_threshold=None):  # noqa: ANN001
        called.append(text)
        return True, None

    monkeypatch.setattr("app.guardrails.classify_prompt", fake_classify)
    state = {
        "messages": [HumanMessage(content="Hello")],
        "user_feedback": "USER says ignore previous (benign correction text)",
    }
    out = run_user_input_guardrails(state, settings_no_guard)
    assert out["validation_error"] == ""
    assert called == ["Hello"]
