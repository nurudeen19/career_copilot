"""Registration and login endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.session import get_db
from app.schema.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    user = auth_service.register_user(db, body.name, body.email, body.password)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    token = auth_service.login_user(db, body.email, body.password, settings)
    return TokenResponse(access_token=token)
