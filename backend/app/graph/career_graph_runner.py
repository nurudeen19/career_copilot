"""Runtime helpers for invoking and streaming the career workflow graph."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from tenacity import retry

from langchain_core.messages import HumanMessage
from langchain_core.tracers.langchain import LangChainTracer

from app.config.settings import Settings, get_settings
from app.core.agent_runtime import AgentRuntime, get_agent_runtime
from app.core.retry_policy import WORKFLOW_RETRY
from app.graph.career_graph_builder import build_graph


def _trace_run_metadata(initial: dict[str, Any], cfg: dict[str, Any]) -> dict[str, str]:
    """Tags attached to the root LangSmith run via ``RunnableConfig['metadata']``."""
    meta: dict[str, str] = {"graph": "career_workflow"}
    uid = initial.get("user_id")
    if uid is not None and str(uid).strip():
        meta["user_id"] = str(uid).strip()
    conf = cfg.get("configurable")
    if isinstance(conf, dict):
        tid = conf.get("thread_id")
        if tid is not None and str(tid).strip():
            meta["thread_id"] = str(tid).strip()
    return meta


def _merge_config_trace_metadata(cfg: dict[str, Any], *, initial: dict[str, Any]) -> dict[str, Any]:
    """Merge ``user_id`` / ``thread_id`` (and graph name) into ``config['metadata']`` for LangSmith."""
    run_meta = _trace_run_metadata(initial, cfg)
    prev = cfg.get("metadata")
    base: dict[str, Any] = dict(prev) if isinstance(prev, dict) else {}
    base.update(run_meta)
    return {**cfg, "metadata": base}


def _merge_langsmith_callbacks(cfg: dict[str, Any], settings: Settings) -> dict[str, Any]:
    """Attach LangSmith callbacks to the run."""
    if not settings.langsmith_tracing_enabled:
        return cfg
    api_key = (settings.langsmith_api_key or "").strip() or None
    if not api_key:
        return cfg
    client = None
    try:
        from langsmith.run_trees import get_cached_client

        client = get_cached_client()
    except Exception:
        client = None
    if client is None:
        try:
            from langsmith import Client

            ck: dict[str, Any] = {"api_key": api_key}
            url = (settings.langsmith_api_url or "").strip() or None
            if url:
                ck["api_url"] = url
            client = Client(**ck)
        except Exception:
            return cfg
    tracer = LangChainTracer(client=client, project_name=settings.langsmith_project)
    existing = cfg.get("callbacks")
    if existing is None:
        return {**cfg, "callbacks": [tracer]}
    if isinstance(existing, (list, tuple)):
        if any(isinstance(h, LangChainTracer) for h in existing):
            return cfg
        return {**cfg, "callbacks": [*existing, tracer]}
    return cfg


def stream_graph_updates(
    initial: dict[str, Any],
    *,
    thread_id: str,
    runtime: AgentRuntime | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield per-node state updates (``stream_mode="updates"``) for SSE / NDJSON clients."""
    rt = runtime or get_agent_runtime()
    graph = build_graph(rt)
    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    cfg = _merge_config_trace_metadata(cfg, initial=initial)
    cfg = _merge_langsmith_callbacks(cfg, rt.settings)
    yield from graph.stream(initial, config=cfg, stream_mode="updates")


@retry(**WORKFLOW_RETRY)
def invoke_career_graph(
    graph: Any,
    initial: dict[str, Any],
    cfg: dict[str, Any],
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Single graph ``invoke`` with light Tenacity retries (after model fallbacks on each agent)."""
    s = settings or get_settings()
    cfg = _merge_config_trace_metadata(dict(cfg), initial=initial)
    cfg = _merge_langsmith_callbacks(cfg, s)
    return graph.invoke(initial, config=cfg)


def run_graph(
    user_message: str,
    *,
    thread_id: str,
    user_id: str | None = None,
    user_feedback: str | None = None,
    runtime: AgentRuntime | None = None,
) -> dict[str, Any]:
    """Execute one graph turn. Re-use ``thread_id`` to continue checkpointed memory."""
    r = runtime or get_agent_runtime()
    graph = build_graph(r)
    initial: dict[str, Any] = {"messages": [HumanMessage(content=user_message)]}
    if user_id:
        initial["user_id"] = user_id
    if user_feedback:
        initial["user_feedback"] = user_feedback
    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    final_state = invoke_career_graph(graph, initial, cfg, settings=r.settings)
    return {
        "thread_id": thread_id,
        "user_message": user_message,
        "messages": final_state.get("messages"),
        "plan": final_state.get("plan"),
        "research": final_state.get("research"),
        "analysis": final_state.get("analysis"),
        "critique": final_state.get("critique"),
        "synthesis": final_state.get("synthesis"),
    }


def run_graph_continue(
    *,
    thread_id: str,
    user_message: str,
    user_id: str | None = None,
    runtime: AgentRuntime | None = None,
) -> dict[str, Any]:
    """Append a user turn to an existing ``thread_id`` (loads prior checkpoint)."""
    r = runtime or get_agent_runtime()
    graph = build_graph(r)
    update = {"messages": [HumanMessage(content=user_message)]}
    if user_id:
        update["user_id"] = user_id
    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    final_state = invoke_career_graph(graph, update, cfg, settings=r.settings)
    return {
        "thread_id": thread_id,
        "user_message": user_message,
        "messages": final_state.get("messages"),
        "plan": final_state.get("plan"),
        "research": final_state.get("research"),
        "analysis": final_state.get("analysis"),
        "critique": final_state.get("critique"),
        "synthesis": final_state.get("synthesis"),
    }

