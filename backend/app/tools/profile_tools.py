"""LangChain tools that read persisted user context."""

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
def get_user_profile_by_id(user_id: str) -> str:
    """Load the user's account name, email, and saved career profile from the database. Argument: user UUID string."""
    uid = (user_id or "").strip()
    if not uid:
        return UserProfileFetchResult(
            found=False,
            user_id="",
            error="user_id is empty; pass a UUID string.",
        ).to_json()
    try:
        parsed = uuid.UUID(uid)
    except ValueError:
        return UserProfileFetchResult(
            found=False,
            user_id=uid,
            error="Invalid UUID format.",
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
