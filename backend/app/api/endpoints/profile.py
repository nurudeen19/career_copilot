"""Authenticated user profile (career context for agents)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import limiter, limit_profile
from app.db.session import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schema.profile import ProfileResponse, ProfileUpdate
from app.services import profile as profile_service

router = APIRouter()


@router.get("", response_model=ProfileResponse)
@limiter.limit(limit_profile)
def get_profile(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfile:
    _ = request.app
    return profile_service.get_or_create_profile(db, user)


@router.patch("", response_model=ProfileResponse)
@limiter.limit(limit_profile)
def patch_profile(
    request: Request,
    body: ProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfile:
    _ = request.app
    return profile_service.update_profile(db, user, body)
