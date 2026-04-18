"""Root API router — include all endpoint modules here."""

from fastapi import APIRouter

from app.api.endpoints import auth as auth_endpoints
from app.api.endpoints import profile as profile_endpoints
from app.api.endpoints import workflow as workflow_endpoints

api_router = APIRouter()
api_router.include_router(auth_endpoints.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile_endpoints.router, prefix="/profile", tags=["profile"])
api_router.include_router(workflow_endpoints.router, prefix="/workflow", tags=["workflow"])
