"""Authenticated user profile (career context for agents)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schema.profile import ProfileResponse, ProfileUpdate
from app.services import profile as profile_service

router = APIRouter()


@router.get("", response_model=ProfileResponse)
def get_profile(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfile:
    return profile_service.get_or_create_profile(db, user)


@router.patch("", response_model=ProfileResponse)
def patch_profile(
    body: ProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfile:
    return profile_service.update_profile(db, user, body)
