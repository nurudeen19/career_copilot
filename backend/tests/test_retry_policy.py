"""Transient error classification for Tenacity / streaming retries."""

from __future__ import annotations

import httpx

from app.core.retry_policy import is_transient_workflow_error


def test_transient_httpx_timeout() -> None:
    assert is_transient_workflow_error(httpx.TimeoutException("timeout"))


def test_transient_httpx_connect() -> None:
    assert is_transient_workflow_error(httpx.ConnectError("refused"))


def test_transient_httpx_remote_protocol() -> None:
    assert is_transient_workflow_error(httpx.RemoteProtocolError("gone"))


def test_non_transient_value_error() -> None:
    assert not is_transient_workflow_error(ValueError("bad input"))


def test_non_transient_http_status_error() -> None:
    exc = httpx.HTTPStatusError(
        "msg",
        request=httpx.Request("GET", "https://example.com"),
        response=httpx.Response(400, request=httpx.Request("GET", "https://example.com")),
    )
    assert not is_transient_workflow_error(exc)
