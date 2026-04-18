"""Environment-backed settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.agents import AgentsConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Career Copilot"
    debug: bool = False

    database_url: str | None = Field(
        default=None,
        description="SQLAlchemy URL, e.g. postgresql+psycopg://user:pass@localhost:5432/career_copilot",
    )
    jwt_secret: str = Field(default="change-me", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    openai_api_key: str | None = None
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    google_api_key: str | None = None
    tavily_api_key: str | None = None

    agents: AgentsConfig = Field(default_factory=AgentsConfig)


@lru_cache
def get_settings() -> Settings:
    return Settings()
