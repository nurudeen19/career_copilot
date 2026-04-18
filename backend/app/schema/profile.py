"""User profile payloads (career context for agents)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdate(BaseModel):
    """Partial update: only sent fields are applied."""

    summary: str | None = None
    profession: str | None = None
    current_salary: int | None = Field(default=None, ge=0)
    salary_target: int | None = Field(default=None, ge=0)
    technologies: str | None = None
    programming_languages: str | None = None
    career_goal: str | None = None
    location: str | None = None
    willing_to_relocate: bool | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    summary: str | None
    profession: str | None
    current_salary: int | None
    salary_target: int | None
    technologies: str | None
    programming_languages: str | None
    career_goal: str | None
    location: str | None
    willing_to_relocate: bool | None
    created_at: datetime
    updated_at: datetime
