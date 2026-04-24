"""HTTP app, database, mail, logging, LangSmith — fields mixed into :class:`~app.config.settings.Settings`."""

from pathlib import Path

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


def default_log_file_dir() -> str:
    return str(Path(__file__).resolve().parents[2] / "logs")


class AppSettings(BaseModel):
    """Core application fields (mixed into ``Settings``)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    app_name: str = "Career Copilot"
    debug: bool = False
    log_level: str = Field(default="INFO")
    log_file_enabled: bool = Field(default=True)
    log_file_dir: str = Field(default_factory=default_log_file_dir)
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ALLOW_ORIGINS",
    )
    database_url: str | None = None
    jwt_secret: str = Field(default="change-me", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    frontend_app_base_url: str = Field(default="http://localhost:5173")
    mailtrap_api_token: str | None = None
    mail_from_email: str = Field(default="noreply@example.com")
    mail_from_name: str = Field(default="Career Copilot")
    auth_dev_auto_verify_email: bool = False

    # Env names mirror LangSmith docs + legacy LANGCHAIN_*; field name maps to LANGSMITH_TRACING_ENABLED too.
    langsmith_tracing_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "LANGSMITH_TRACING_V2",
            "LANGCHAIN_TRACING_V2",
            "LANGSMITH_TRACING_ENABLED",
            "LANGCHAIN_TRACING_ENABLED",
        ),
    )
    langsmith_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LANGSMITH_API_KEY",
            "LANGCHAIN_API_KEY",
        ),
    )
    langsmith_project: str = Field(
        default="career-copilot",
        validation_alias=AliasChoices(
            "LANGSMITH_PROJECT",
            "LANGCHAIN_PROJECT",
        ),
    )
    langsmith_api_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LANGSMITH_ENDPOINT",
            "LANGCHAIN_ENDPOINT",
            "LANGSMITH_API_URL",
            "LANGCHAIN_API_URL",
        ),
    )
