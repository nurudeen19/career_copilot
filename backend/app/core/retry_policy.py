"""Transient-error detection and Tenacity defaults for graph invoke, streaming, and per-agent calls.

LangChain ``with_fallbacks`` (see ``build_chat_model``) handles primary→backup model failures first.
Tenacity here only covers remaining transient faults (HTTP timeouts, 429/5xx, etc.) with short retries.
"""

from __future__ import annotations

import logging
import ssl

import httpx
from tenacity import before_sleep_log, retry_if_exception, stop_after_attempt, wait_exponential

_log = logging.getLogger("app.retry")

_OPENAI_RETRY: tuple[type[BaseException], ...] = ()
try:
    from openai import APIConnectionError, RateLimitError  # type: ignore[import-not-found]

    _OPENAI_RETRY = (APIConnectionError, RateLimitError)
except ImportError:  # pragma: no cover
    pass


def is_transient_workflow_error(exc: BaseException) -> bool:
    """Network / overload / remote blips worth retrying; not validation, auth, or bad requests."""
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, ssl.SSLError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        return code in (408, 425, 429, 500, 502, 503, 504)
    if _OPENAI_RETRY and isinstance(exc, _OPENAI_RETRY):
        return True
    return False


WORKFLOW_RETRY = dict(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=6),
    retry=retry_if_exception(is_transient_workflow_error),
    reraise=True,
    before_sleep=before_sleep_log(_log, logging.WARNING),
)

# Per-agent invoke: one retry after LangChain fallbacks (if configured) exhaust.
AGENT_INVOKE_POLICY = dict(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.4, min=0.5, max=5),
    retry=retry_if_exception(is_transient_workflow_error),
    reraise=True,
    before_sleep=before_sleep_log(_log, logging.INFO),
)
