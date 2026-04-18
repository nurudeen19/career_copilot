"""Root API router — include all endpoint modules here."""

from fastapi import APIRouter

from app.api.endpoints import auth as auth_endpoints

api_router = APIRouter()
api_router.include_router(auth_endpoints.router, prefix="/auth", tags=["auth"])
