"""User registration and login logic."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def register_user(db: Session, name: str, email: str, password: str) -> User:
    normalized = email.lower().strip()
    existing = db.scalar(select(User).where(User.email == normalized))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=name.strip(),
        email=normalized,
        hashed_password=_hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str, settings: Settings) -> str:
    normalized = email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized))
    if user is None or not _verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _create_access_token(user.id, settings)
