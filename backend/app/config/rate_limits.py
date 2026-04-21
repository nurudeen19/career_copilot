"""SlowAPI limits (nested ``rate_limits`` on ``Settings`` → env ``RATE_LIMITS__*``)."""

from pydantic import BaseModel, ConfigDict, Field


class RateLimitsSettings(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    enabled: bool = True
    login: str = "10/minute"
    signup: str = "5/minute"
    auth_email: str = "5/minute"
    verify_email: str = "10/minute"
    reset_password: str = "10/minute"
    profile: str = "10/minute"
    workflow_stream: str = "6/minute"
    health: str = "60/minute"
