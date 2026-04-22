"""Request and response models for registration and login."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Reasonable upper bound (Argon2 allows much longer; caps request size / memory abuse).
MAX_PASSWORD_LENGTH = 512


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=MAX_PASSWORD_LENGTH)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    created_at: datetime
    email_verified: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class EmailRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    user_id: uuid.UUID
    token: str = Field(min_length=10, max_length=512)


class MessageResponse(BaseModel):
    detail: str


class ResetPasswordRequest(BaseModel):
    user_id: uuid.UUID
    token: str = Field(min_length=10, max_length=256)
    password: str = Field(min_length=8, max_length=MAX_PASSWORD_LENGTH)
