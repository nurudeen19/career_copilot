"""Per-invocation context for LangGraph agent tools (set by the graph, read by tools)."""

from __future__ import annotations

from contextvars import ContextVar

# UUID string of the authenticated user for the current agent graph invoke (no cross-user reads).
workflow_user_id: ContextVar[str | None] = ContextVar("workflow_user_id", default=None)
