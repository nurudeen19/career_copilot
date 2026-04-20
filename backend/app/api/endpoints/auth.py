"""Registration, login, verification, and password reset endpoints."""

import html
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.session import get_db
from app.schema.auth import (
    EmailRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    user = auth_service.register_user(db, body.name, body.email, body.password, settings)
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        email_verified=user.email_verified_at is not None,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    token = auth_service.login_user(db, body.email, body.password, settings)
    return TokenResponse(access_token=token)


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(
    token: str = Query(min_length=10),
    user_id: uuid.UUID = Query(alias="user_id"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    auth_service.verify_email_with_token(db, user_id, token, settings)
    return MessageResponse(detail="Email verified. You can sign in.")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    body: EmailRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    auth_service.resend_verification_email(db, body.email, settings)
    return MessageResponse(
        detail="If that address is registered and not yet verified, a new message was sent.",
    )


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_form(
    token: str = Query(min_length=10),
    user_id: uuid.UUID = Query(alias="user_id"),
) -> HTMLResponse:
    """Minimal browser page to complete a reset (link from email)."""
    safe_t = html.escape(token, quote=True)
    safe_uid = html.escape(str(user_id), quote=True)
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Reset password</title></head>
<body>
  <h1>Reset password</h1>
  <form id="reset-form">
    <input type="hidden" id="user_id" value="{safe_uid}"/>
    <input type="hidden" id="token" value="{safe_t}"/>
    <p><label>New password <input type="password" id="password" minlength="8" required/></label></p>
    <p><button type="submit">Update password</button></p>
    <p id="msg"></p>
  </form>
  <script>
    document.getElementById("reset-form").addEventListener("submit", async (e) => {{
      e.preventDefault();
      const body = {{
        user_id: document.getElementById("user_id").value,
        token: document.getElementById("token").value,
        password: document.getElementById("password").value,
      }};
      const r = await fetch("/auth/reset-password", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(body),
      }});
      const msg = document.getElementById("msg");
      if (r.ok) {{ msg.textContent = "Password updated. You can close this page."; }}
      else {{ msg.textContent = await r.text(); }}
    }});
  </script>
</body></html>"""
    return HTMLResponse(page)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    body: EmailRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    auth_service.request_password_reset(db, body.email, settings)
    return MessageResponse(
        detail="If that address is registered, password reset instructions were sent.",
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    auth_service.reset_password_with_token(db, body.user_id, body.token, body.password, settings)
    return MessageResponse(detail="Password updated. You can sign in with your new password.")
