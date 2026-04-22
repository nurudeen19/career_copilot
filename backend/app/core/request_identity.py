"""Decode JWT ``sub`` for access logs (no DB hit; invalid/expired tokens → ``None``)."""

from __future__ import annotations

from fastapi import Request
from jose import JWTError, jwt

from app.config.settings import get_settings


def jwt_sub_for_logs(request: Request) -> str | None:
    """Return the JWT subject (user id) when the Bearer token is present and valid."""
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    try:
        s = get_settings()
        payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
        sub = payload.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None
