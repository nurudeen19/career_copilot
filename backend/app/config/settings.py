"""Application settings: domain classes are mixins on ``Settings``; views are ``cast(self)`` (single source of truth)."""

from __future__ import annotations

from functools import lru_cache
from typing import cast

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.agents import AgentsConfig
from app.config.app_settings import AppSettings
from app.config.prompt_guard_config import PromptGuardSettings
from app.config.rate_limits import RateLimitsSettings
from app.config.workflow import WorkflowSettings


class Settings(
    AppSettings,
    AgentsConfig,
    WorkflowSettings,
    RateLimitsSettings,
    PromptGuardSettings,
    BaseSettings,
):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def app_core(self) -> AppSettings:
        return cast(AppSettings, self)

    @property
    def agents(self) -> AgentsConfig:
        return cast(AgentsConfig, self)

    @property
    def workflow(self) -> WorkflowSettings:
        return cast(WorkflowSettings, self)

    @property
    def rate_limits(self) -> RateLimitsSettings:
        return cast(RateLimitsSettings, self)

    @property
    def prompt_guard(self) -> PromptGuardSettings:
        return cast(PromptGuardSettings, self)


@lru_cache
def get_settings() -> Settings:
    return Settings()
