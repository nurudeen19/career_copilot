"""Per-agent invoke with Tenacity retries and non-transient fallbacks so the graph can finish."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from tenacity import Retrying

from app.core.retry_policy import AGENT_INVOKE_POLICY, is_transient_workflow_error

_log = logging.getLogger(__name__)


def invoke_agent_with_resilience(
    call: Callable[[], dict[str, Any]],
    *,
    step: str,
    fallback: Callable[[BaseException], dict[str, Any]],
) -> dict[str, Any]:
    """
    Run ``call()`` (typically ``agent_graph.invoke``) with a short Tenacity retry on transient HTTP errors.

    Primary model failures are handled first by LangChain ``with_fallbacks`` when configured on the chat model.
    After retries, **transient** errors are re-raised (outer graph / SSE layer may retry).
    **Non-transient** or exhausted-transient failures use ``fallback(exc)`` so the workflow continues.
    """
    r = Retrying(**AGENT_INVOKE_POLICY)
    try:
        return r(call)
    except Exception as exc:
        if is_transient_workflow_error(exc):
            _log.warning("agent_step_transient_exhausted step=%s: %s", step, exc)
            raise
        # Expected path when the model or parser fails: graph continues with node fallback.
        _log.info(
            "agent_step_fallback step=%s err_type=%s err=%s",
            step,
            type(exc).__name__,
            exc,
        )
        _log.debug("agent_step_fallback traceback step=%s", step, exc_info=True)
        return fallback(exc)
