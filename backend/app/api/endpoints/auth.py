"""Registration, login, verification, and password reset endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config.settings import Settings, get_settings
from app.core.rate_limit import (
    limiter,
    limit_auth_email,
    limit_login,
    limit_register,
    limit_reset_password,
    limit_verify_email,
    limit_profile,
)
from app.db.session import get_db
from app.models.user import User
from app.schema.auth import (
    EmailRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse)
@limiter.limit(limit_register)
def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    _ = request.app
    user = auth_service.register_user(db, body.name, body.email, body.password, settings)
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        email_verified=user.email_verified_at is not None,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(limit_login)
def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    _ = request.app
    token, user = auth_service.login_user(db, body.email, body.password, settings)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
            email_verified=user.email_verified_at is not None,
        ),
    )


@router.get("/me", response_model=UserResponse)
@limiter.limit(limit_profile)
def read_current_user(
    request: Request,
    user: User = Depends(get_current_user),
) -> UserResponse:
    _ = request.app
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        email_verified=user.email_verified_at is not None,
    )


@router.post("/verify-email", response_model=MessageResponse)
@limiter.limit(limit_verify_email)
def verify_email(
    request: Request,
    body: VerifyEmailRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Called from the SPA after the user opens the verification link (token not logged as a full URL path)."""
    _ = request.app
    auth_service.verify_email_with_token(db, body.user_id, body.token, settings)
    return MessageResponse(detail="Email verified. You can sign in.")


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit(limit_auth_email)
def resend_verification(
    request: Request,
    body: EmailRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    _ = request.app
    auth_service.resend_verification_email(db, body.email, settings)
    return MessageResponse(
        detail="If that address is registered and not yet verified, a new message was sent.",
    )


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(limit_auth_email)
def forgot_password(
    request: Request,
    body: EmailRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    _ = request.app
    auth_service.request_password_reset(db, body.email, settings)
    return MessageResponse(
        detail="If that address is registered, password reset instructions were sent.",
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit(limit_reset_password)
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    _ = request.app
    auth_service.reset_password_with_token(db, body.user_id, body.token, body.password, settings)
    return MessageResponse(detail="Password updated. You can sign in with your new password.")
