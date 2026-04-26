"""Structured JSON logging formatter."""

from __future__ import annotations

import io
import json
import logging

import pytest

from app.core.logging_config import StructuredJsonFormatter, reset_logging_for_tests


@pytest.fixture(autouse=True)
def _reset_logging() -> None:
    yield
    reset_logging_for_tests()


def test_structured_json_formatter_emits_parseable_object() -> None:
    buf = io.StringIO()
    log = logging.getLogger("test.json")
    log.handlers.clear()
    log.setLevel(logging.INFO)
    log.propagate = False
    h = logging.StreamHandler(buf)
    h.setFormatter(StructuredJsonFormatter())
    log.addHandler(h)

    log.info(
        "hello",
        extra={"event": "test_event", "thread_id": "abc-123"},
    )
    line = buf.getvalue().strip()
    data = json.loads(line)
    assert data["level"] == "INFO"
    assert data["logger"] == "test.json"
    assert data["message"] == "hello"
    assert data["event"] == "test_event"
    assert data["thread_id"] == "abc-123"
    assert "timestamp" in data
    assert data["src_func"] == "test_structured_json_formatter_emits_parseable_object"
