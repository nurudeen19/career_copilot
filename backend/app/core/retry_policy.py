"""Shared transient-error detection and Tenacity defaults for graph invoke / stream retries."""

from __future__ import annotations

import httpx
from tenacity import retry_if_exception, stop_after_attempt, wait_exponential

_OPENAI_RETRY: tuple[type[BaseException], ...] = ()
try:
    from openai import APIConnectionError, RateLimitError  # type: ignore[import-not-found]

    _OPENAI_RETRY = (APIConnectionError, RateLimitError)
except ImportError:  # pragma: no cover
    pass


def is_transient_workflow_error(exc: BaseException) -> bool:
    """HTTP / provider blips worth retrying; not validation or auth failures."""
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)):
        return True
    if _OPENAI_RETRY and isinstance(exc, _OPENAI_RETRY):
        return True
    return False


WORKFLOW_RETRY = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
    retry=retry_if_exception(is_transient_workflow_error),
    reraise=True,
)
