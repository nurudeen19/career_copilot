"""HTTP contract for running the career LangGraph workflow."""

from __future__ import annotations

import uuid
from typing import Self

from pydantic import BaseModel, Field, model_validator


class WorkflowStreamRequest(BaseModel):
    """Body for ``POST /workflow/stream``. After guardrails inside the graph pass, the same payload drives the run."""

    message: str = Field(
        default="",
        max_length=48_000,
        description="User message (new turn or follow-up). May be empty when sending only ``user_feedback``.",
    )
    thread_id: uuid.UUID | None = Field(
        default=None,
        description="Checkpoint thread. Omit to start a new conversation.",
    )
    user_feedback: str | None = Field(
        default=None,
        max_length=48_000,
        description="If set, routes through the feedback node after validation (typically with an existing ``thread_id``).",
    )

    @model_validator(mode="after")
    def require_some_user_text(self) -> Self:
        if not (self.message or "").strip() and not (self.user_feedback or "").strip():
            raise ValueError("Provide a non-empty message and/or user_feedback.")
        return self
