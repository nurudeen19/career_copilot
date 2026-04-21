"""App settings from ``.env`` (composed nested blocks)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.agents import AgentsConfig
from app.config.prompt_guard_config import PromptGuardSettings
from app.config.rate_limits import RateLimitsSettings
from app.config.workflow import WorkflowSettings


def _default_log_file_dir() -> str:
    return str(Path(__file__).resolve().parents[2] / "logs")


# Flat env names (provider defaults); merged into ``agents`` when nested key empty.
_AGENT_API_KEY_ENV: tuple[tuple[str, str], ...] = (
    ("OPENAI_API_KEY", "openai_api_key"),
    ("GROQ_API_KEY", "groq_api_key"),
    ("OPENROUTER_API_KEY", "openrouter_api_key"),
    ("GOOGLE_API_KEY", "google_api_key"),
    ("TAVILY_API_KEY", "tavily_api_key"),
    ("BRAVE_SEARCH_API_KEY", "brave_search_api_key"),
)


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
    log_level: str = Field(default="INFO")
    log_file_enabled: bool = Field(default=True)
    log_file_dir: str = Field(default_factory=_default_log_file_dir)
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

    rate_limits: RateLimitsSettings = Field(default_factory=RateLimitsSettings)

    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = Field(default="career-copilot")

    workflow: WorkflowSettings = Field(default_factory=WorkflowSettings)
    prompt_guard: PromptGuardSettings = Field(default_factory=PromptGuardSettings)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)

    @model_validator(mode="before")
    @classmethod
    def _merge_flat_env_into_nested(cls, data: Any) -> Any:
        """HF token + LLM/search keys: allow flat env names (not only nested)."""
        if not isinstance(data, dict):
            return data
        out = dict(data)

        pg = dict(out.get("prompt_guard") or {})
        if not str(pg.get("huggingface_token") or "").strip():
            for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_TOKEN"):
                v = out.get(key) or os.environ.get(key)
                if v:
                    pg["huggingface_token"] = v
                    break
        if pg:
            out["prompt_guard"] = {**(out.get("prompt_guard") or {}), **pg}

        ag = dict(out.get("agents") or {})
        for env_name, field in _AGENT_API_KEY_ENV:
            if not str(ag.get(field) or "").strip():
                v = out.get(env_name) or os.environ.get(env_name)
                if v:
                    ag[field] = v
        out["agents"] = {**(out.get("agents") or {}), **ag}

        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()
