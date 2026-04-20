"""Workflow request schema validation."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.schema.workflow import WorkflowStreamRequest


def test_workflow_requires_some_text() -> None:
    with pytest.raises(ValidationError):
        WorkflowStreamRequest(message="", user_feedback=None)


def test_workflow_message_only() -> None:
    m = WorkflowStreamRequest(message="What about product roles?")
    assert m.message.strip()
    assert m.thread_id is None


def test_workflow_feedback_only() -> None:
    m = WorkflowStreamRequest(message="", user_feedback="That answer felt generic.")
    assert m.user_feedback


def test_workflow_with_thread_id() -> None:
    tid = uuid.uuid4()
    m = WorkflowStreamRequest(message="Follow up", thread_id=tid)
    assert m.thread_id == tid
