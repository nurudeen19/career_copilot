"""SlowAPI limits (mixed into ``Settings``)."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class RateLimitsSettings(BaseModel):
    """``RATE_LIMIT_ENABLED``, ``RATE_LIMIT_LOGIN``, …"""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(default=True, validation_alias=AliasChoices("RATE_LIMIT_ENABLED"))
    login: str = Field(default="10/minute", validation_alias=AliasChoices("RATE_LIMIT_LOGIN"))
    signup: str = Field(default="5/minute", validation_alias=AliasChoices("RATE_LIMIT_SIGNUP"))
    auth_email: str = Field(default="5/minute", validation_alias=AliasChoices("RATE_LIMIT_AUTH_EMAIL"))
    verify_email: str = Field(default="10/minute", validation_alias=AliasChoices("RATE_LIMIT_VERIFY_EMAIL"))
    reset_password: str = Field(default="10/minute", validation_alias=AliasChoices("RATE_LIMIT_RESET_PASSWORD"))
    profile: str = Field(default="10/minute", validation_alias=AliasChoices("RATE_LIMIT_PROFILE"))
    workflow_stream: str = Field(default="6/minute", validation_alias=AliasChoices("RATE_LIMIT_WORKFLOW_STREAM"))
    health: str = Field(default="60/minute", validation_alias=AliasChoices("RATE_LIMIT_HEALTH"))
