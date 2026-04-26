"""Pydantic settings: env binding and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_settings_defaults_for_optional_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROMPT_GUARD_MALICIOUS_THRESHOLD", raising=False)
    s = Settings(
        jwt_secret="adequate-secret-here",
        database_url=None,
    )
    assert s.app_name == "Career Copilot"
    assert s.database_url is None
    assert s.log_level.upper() == "INFO"
    assert s.log_file_json is True
    assert s.log_console_json is False
    assert s.log_color is True
    assert s.prompt_guard.model_id == "meta-llama/Llama-Prompt-Guard-2-86M"
    assert s.prompt_guard.malicious_probability_threshold == 0.15


def test_settings_jwt_secret_min_length() -> None:
    with pytest.raises(ValidationError):
        Settings(jwt_secret="short")


def test_settings_log_level_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "warning")
    s = Settings()
    assert s.log_level == "warning"


def test_settings_log_file_json_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_JSON", "false")
    s = Settings()
    assert s.log_file_json is False


def test_settings_log_console_json_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_CONSOLE_JSON", "true")
    s = Settings()
    assert s.log_console_json is True


def test_settings_log_color_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_COLOR", "false")
    s = Settings()
    assert s.log_color is False


def test_settings_database_url_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    url = f"sqlite+pysqlite:///{tmp_path / 's.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    s = Settings()
    assert s.database_url == url


def test_openai_api_key_on_agents_mixin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-root-test")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    s = Settings()
    assert s.agents.openai_api_key == "sk-root-test"
    assert s.openai_api_key == "sk-root-test"
    get_settings.cache_clear()
