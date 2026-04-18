"""Tool payload: fetch career profile by user id (no PII beyond id)."""

from pydantic import BaseModel, Field

from app.schema.profile import ProfileResponse


class UserProfileFetchResult(BaseModel):
    """JSON returned by ``get_user_profile_by_id`` (stringified for the LLM)."""

    found: bool = Field(description="Whether a user row exists for the given id.")
    user_id: str = Field(description="UUID string that was requested.")
    profile: ProfileResponse | None = Field(
        default=None,
        description="Career profile row when present (may be null if not created yet).",
    )
    error: str | None = Field(default=None, description="Set when the lookup could not run.")

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)
