"""Root API router — include all endpoint modules here."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.endpoints import auth as auth_endpoints
from app.api.endpoints import health as health_endpoints
from app.api.endpoints import profile as profile_endpoints
from app.api.endpoints import workflow as workflow_endpoints


class APIInfo(BaseModel):
    """Basic API information."""
    name: str
    version: str
    description: str


api_router = APIRouter()


@api_router.get("/", response_model=APIInfo, tags=["info"])
async def root():
    """Root endpoint showing basic API information."""
    return APIInfo(
        name="Career Copilot",
        version="0.1.0",
        description="Agentic career advisor chat API",
    )


api_router.include_router(health_endpoints.router, tags=["health"])
api_router.include_router(auth_endpoints.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile_endpoints.router, prefix="/profile", tags=["profile"])
api_router.include_router(workflow_endpoints.router, prefix="/workflow", tags=["workflow"])
