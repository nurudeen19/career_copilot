"""Planner structured output: schema records model decisions; handoff is required."""

import pytest
from pydantic import ValidationError

from app.schema.agent_outputs import PlannerAgentOutput


def test_handoff_is_required() -> None:
    with pytest.raises(ValidationError):
        PlannerAgentOutput.model_validate({})


def test_model_chosen_handoff_is_preserved() -> None:
    p = PlannerAgentOutput(
        handoff="research",
        subtasks=["help", "x"],
        assistant_message=None,
    )
    assert p.handoff == "research"


def test_explicit_casual_handoff() -> None:
    p = PlannerAgentOutput(
        handoff="user_casual_redirect",
        assistant_message="Hi! What career topic can I help with?",
    )
    assert p.handoff == "user_casual_redirect"


def test_non_research_handoff_gets_default_message() -> None:
    p = PlannerAgentOutput(handoff="user_clarify", assistant_message="  ")
    assert p.assistant_message


def test_research_handoff_does_not_force_message() -> None:
    p = PlannerAgentOutput(handoff="research", assistant_message="  ")
    assert p.assistant_message is None
