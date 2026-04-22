"""LangChain tools that read persisted user context (bound to the workflow user)."""

from __future__ import annotations

import uuid

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import open_tool_session
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schema.profile import ProfileResponse
from app.schema.profile_tool import UserProfileFetchResult
from app.tools.runtime_context import workflow_user_id


def _fetch(session: Session, user_id: uuid.UUID) -> UserProfileFetchResult:
    user = session.get(User, user_id)
    if user is None:
        return UserProfileFetchResult(found=False, user_id=str(user_id), error="No user with this id.")
    profile = session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    pr: ProfileResponse | None = None
    if profile is not None:
        pr = ProfileResponse.model_validate(profile)
    return UserProfileFetchResult(
        found=True,
        user_id=str(user.id),
        profile=pr,
    )


@tool
def get_my_saved_profile() -> str:
    """
    Load the authenticated user's saved career profile from the database.
    Takes no arguments — the server binds this call to the current workflow user.
    """
    raw = (workflow_user_id.get() or "").strip()
    if not raw:
        return UserProfileFetchResult(
            found=False,
            user_id="",
            error="No workflow user context; profile cannot be loaded.",
        ).to_json()
    try:
        parsed = uuid.UUID(raw)
    except ValueError:
        return UserProfileFetchResult(
            found=False,
            user_id=raw,
            error="Invalid workflow user id.",
        ).to_json()

    try:
        db = open_tool_session()
    except RuntimeError as exc:
        return UserProfileFetchResult(
            found=False,
            user_id=str(parsed),
            error=str(exc),
        ).to_json()

    try:
        return _fetch(db, parsed).to_json()
    finally:
        db.close()
