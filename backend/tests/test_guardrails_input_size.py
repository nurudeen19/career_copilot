"""Input size limits (no HF model)."""

from __future__ import annotations

from app.config.settings import Settings
from app.guardrails.input_size import validate_input_size


def test_validate_input_size_within_limits() -> None:
    s = Settings(jwt_secret="x" * 12, max_user_input_chars=1000, max_user_estimated_tokens=500)
    assert validate_input_size("hello", s) is None


def test_validate_input_size_too_many_chars() -> None:
    s = Settings(jwt_secret="x" * 12, max_user_input_chars=10, max_user_estimated_tokens=500)
    err = validate_input_size("x" * 20, s)
    assert err is not None
    assert "too long" in err.lower()


def test_validate_input_size_estimated_tokens() -> None:
    s = Settings(jwt_secret="x" * 12, max_user_input_chars=100_000, max_user_estimated_tokens=2)
    # len 40 → est_tokens 10 > 2
    text = "word " * 8  # 40 chars
    err = validate_input_size(text, s)
    assert err is not None
    assert "token" in err.lower()
