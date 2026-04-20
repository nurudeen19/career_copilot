"""User registration, login, email verification, and password reset."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.models.user import User
from app.services.mail import send_transactional_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_log = logging.getLogger(__name__)

VERIFY_TTL = timedelta(hours=48)
RESET_TTL = timedelta(hours=2)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _token_digest(settings: Settings, raw: str) -> str:
    return hmac.new(
        settings.jwt_secret.encode("utf-8"),
        raw.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _public_base(settings: Settings) -> str:
    return settings.public_app_base_url.rstrip("/")


def _create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def register_user(db: Session, name: str, email: str, password: str, settings: Settings) -> User:
    if not settings.auth_dev_auto_verify_email and not settings.mailtrap_api_token:
        raise HTTPException(
            status_code=503,
            detail="Transactional email is not configured (set MAILTRAP_API_TOKEN or AUTH_DEV_AUTO_VERIFY_EMAIL).",
        )
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
    db.flush()

    now = datetime.now(timezone.utc)
    if settings.auth_dev_auto_verify_email:
        user.email_verified_at = now
        user.email_verification_token_digest = None
        user.email_verification_expires_at = None
        db.commit()
        db.refresh(user)
        return user

    raw = secrets.token_urlsafe(32)
    user.email_verification_token_digest = _token_digest(settings, raw)
    user.email_verification_expires_at = now + VERIFY_TTL
    try:
        link = f"{_public_base(settings)}/auth/verify-email?token={raw}&user_id={user.id}"
        send_transactional_email(
            settings,
            to_email=user.email,
            subject="Verify your Career Copilot account",
            text=(
                f"Hi {user.name},\n\n"
                "Please confirm your email by opening this link (valid 48 hours):\n\n"
                f"{link}\n\n"
                "If you did not sign up, you can ignore this message.\n"
            ),
            html=(
                f"<p>Hi {user.name},</p>"
                "<p>Please confirm your email by clicking the link below (valid 48 hours):</p>"
                f'<p><a href="{link}">Verify email</a></p>'
                "<p>If you did not sign up, you can ignore this message.</p>"
            ),
        )
    except Exception as e:
        db.rollback()
        _log.exception("Verification email failed for %s", user.email)
        raise HTTPException(
            status_code=503,
            detail="Unable to send verification email. Try again later.",
        ) from e

    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str, settings: Settings) -> tuple[str, User]:
    normalized = email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized))
    if user is None or not _verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.email_verified_at is None:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Check your inbox or request a new verification link.",
        )
    return _create_access_token(user.id, settings), user


def verify_email_with_token(db: Session, user_id: uuid.UUID, token: str, settings: Settings) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    if user.email_verified_at is not None:
        return
    digest = _token_digest(settings, token)
    now = datetime.now(timezone.utc)
    exp = _as_utc(user.email_verification_expires_at)
    if (
        user.email_verification_token_digest is None
        or not secrets.compare_digest(user.email_verification_token_digest, digest)
        or exp is None
        or exp < now
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    user.email_verified_at = now
    user.email_verification_token_digest = None
    user.email_verification_expires_at = None
    db.commit()


def resend_verification_email(db: Session, email: str, settings: Settings) -> None:
    """Idempotent; avoids email enumeration."""
    normalized = email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized))
    if user is None or user.email_verified_at is not None:
        return
    if not settings.auth_dev_auto_verify_email and not settings.mailtrap_api_token:
        raise HTTPException(
            status_code=503,
            detail="Transactional email is not configured (set MAILTRAP_API_TOKEN).",
        )
    if settings.auth_dev_auto_verify_email:
        user.email_verified_at = datetime.now(timezone.utc)
        user.email_verification_token_digest = None
        user.email_verification_expires_at = None
        db.commit()
        return

    raw = secrets.token_urlsafe(32)
    user.email_verification_token_digest = _token_digest(settings, raw)
    user.email_verification_expires_at = datetime.now(timezone.utc) + VERIFY_TTL
    db.flush()
    try:
        link = f"{_public_base(settings)}/auth/verify-email?token={raw}&user_id={user.id}"
        send_transactional_email(
            settings,
            to_email=user.email,
            subject="Verify your Career Copilot account",
            text=(
                f"Hi {user.name},\n\n"
                "Please confirm your email by opening this link (valid 48 hours):\n\n"
                f"{link}\n\n"
                "If you did not sign up, you can ignore this message.\n"
            ),
            html=(
                f"<p>Hi {user.name},</p>"
                "<p>Please confirm your email by clicking the link below (valid 48 hours):</p>"
                f'<p><a href="{link}">Verify email</a></p>'
                "<p>If you did not sign up, you can ignore this message.</p>"
            ),
        )
    except Exception:
        db.rollback()
        _log.exception("Resend verification email failed for %s", user.email)
        raise HTTPException(
            status_code=503,
            detail="Unable to send verification email. Try again later.",
        ) from None
    db.commit()


def request_password_reset(db: Session, email: str, settings: Settings) -> None:
    """Always succeeds from the caller's perspective (no enumeration)."""
    normalized = email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized))
    if user is None:
        return
    if settings.auth_dev_auto_verify_email:
        _log.debug("password reset email skipped (auth_dev_auto_verify_email)")
        return
    if not settings.mailtrap_api_token:
        _log.warning("password reset requested but mailtrap_api_token is not set")
        return

    raw = secrets.token_urlsafe(32)
    user.password_reset_token_digest = _token_digest(settings, raw)
    user.password_reset_expires_at = datetime.now(timezone.utc) + RESET_TTL
    db.flush()
    try:
        link = f"{_public_base(settings)}/auth/reset-password?token={raw}&user_id={user.id}"
        send_transactional_email(
            settings,
            to_email=user.email,
            subject="Reset your Career Copilot password",
            text=(
                f"Hi {user.name},\n\n"
                "We received a request to reset your password. Open this link (valid 2 hours):\n\n"
                f"{link}\n\n"
                "Then submit your new password to POST /auth/reset-password with JSON body "
                '{"token","user_id","password"} using the same token and user_id from this link.\n\n'
                "If you did not request a reset, ignore this email.\n"
            ),
            html=(
                f"<p>Hi {user.name},</p>"
                "<p>We received a request to reset your password. Open the link below (valid 2 hours) "
                "to choose a new password in your browser:</p>"
                f'<p><a href="{link}">Reset password</a></p>'
                "<p>You can also call <code>POST /auth/reset-password</code> with JSON "
                "<code>token</code>, <code>user_id</code>, and <code>password</code>.</p>"
                "<p>If you did not request a reset, ignore this email.</p>"
            ),
        )
    except Exception:
        db.rollback()
        _log.exception("Password reset email failed for %s", user.email)
        raise HTTPException(
            status_code=503,
            detail="Unable to send password reset email. Try again later.",
        ) from None
    db.commit()


def reset_password_with_token(
    db: Session,
    user_id: uuid.UUID,
    token: str,
    new_password: str,
    settings: Settings,
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    digest = _token_digest(settings, token)
    now = datetime.now(timezone.utc)
    exp = _as_utc(user.password_reset_expires_at)
    if (
        user.password_reset_token_digest is None
        or not secrets.compare_digest(user.password_reset_token_digest, digest)
        or exp is None
        or exp < now
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    user.hashed_password = _hash_password(new_password)
    user.password_reset_token_digest = None
    user.password_reset_expires_at = None
    db.commit()
