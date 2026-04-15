"""Environment-backed settings (no extra deps)."""

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "Career Copilot"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings(
        debug=os.getenv("DEBUG", "").lower() in ("1", "true", "yes"),
    )
