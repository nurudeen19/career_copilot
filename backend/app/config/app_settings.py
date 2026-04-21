"""HTTP app, database, mail, logging, LangSmith — env on the merged :class:`~app.config.settings.Settings`."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


def default_log_file_dir() -> str:
    return str(Path(__file__).resolve().parents[2] / "logs")


class AppSettings(BaseModel):
    """Core application fields (mixed into ``Settings``)."""

    model_config = ConfigDict(extra="ignore")

    app_name: str = "Career Copilot"
    debug: bool = False
    log_level: str = Field(default="INFO")
    log_file_enabled: bool = Field(default=True)
    log_file_dir: str = Field(default_factory=default_log_file_dir)
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173",
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
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = Field(default="career-copilot")
