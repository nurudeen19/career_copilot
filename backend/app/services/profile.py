"""User profile read/update."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.schema.profile import ProfileUpdate


def get_or_create_profile(db: Session, user: User) -> UserProfile:
    row = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if row is not None:
        return row
    row = UserProfile(user_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_profile(db: Session, user: User, data: ProfileUpdate) -> UserProfile:
    profile = get_or_create_profile(db, user)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
