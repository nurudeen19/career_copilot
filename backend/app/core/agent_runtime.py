"""Process-wide chat models and LangChain ``create_agent`` graphs (one place)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel

from app.config.agents import AgentName
from app.config.settings import Settings, get_settings
from app.llm.providers import build_chat_model


def _agent_cache_key(
    name: AgentName,
    response_format: Any,
    tools: Sequence[Any] | None,
) -> tuple[Any, ...]:
    """Stable cache key per agent, tools, and optional structured-output schema."""
    tool_names = tuple(getattr(t, "name", type(t).__name__) for t in (tools or ()))
    if response_format is None:
        return (name, None, tool_names)
    if isinstance(response_format, type):
        return (name, response_format, tool_names)
    return (name, id(response_format), tool_names)


def _model_for_create_agent(model: Any, *, structured: bool) -> Any:
    """``create_agent`` only auto-detects provider JSON schema on ``BaseChatModel`` (or a model id string).

    ``with_fallbacks`` wraps the chat model in ``RunnableWithFallbacks``, which is not a
    ``BaseChatModel``; LangChain then falls back to tool-style structured output and the
    graph often ends without ``structured_response``. Use the primary runnable for
    structured agents (resilience stays on the graph invoke path where applicable).
    """
    if not structured:
        return model
    if isinstance(model, BaseChatModel):
        return model
    inner = getattr(model, "runnable", None)
    if isinstance(inner, BaseChatModel):
        return inner
    return model


class AgentRuntime:
    """Caches chat models and compiled agents from ``initialize_agent``."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._chat_models: dict[AgentName, Any] = {}
        self._agents: dict[tuple[Any, ...], Any] = {}

    @property
    def settings(self) -> Settings:
        return self._settings

    def chat_model(self, name: AgentName) -> Any:
        if name not in self._chat_models:
            agent_llm_config = getattr(self._settings.agents, name)
            self._chat_models[name] = build_chat_model(agent_llm_config, self._settings)
        return self._chat_models[name]

    def initialize_agent(
        self,
        name: AgentName,
        *,
        instructions: str,
        tools: Sequence[Any] | None = None,
        response_format: Any | None = None,
    ) -> Any:
        """Return a cached LangChain agent, or build it with ``create_agent``."""
        key = _agent_cache_key(name, response_format, tools)
        if key in self._agents:
            return self._agents[key]

        tool_list = list(tools) if tools else []
        kwargs: dict[str, Any] = {
            "tools": tool_list,
            "system_prompt": instructions,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        model = _model_for_create_agent(
            self.chat_model(name),
            structured=response_format is not None,
        )
        graph = create_agent(model, **kwargs)
        self._agents[key] = graph
        return graph

    def clear(self) -> None:
        self._chat_models.clear()
        self._agents.clear()


_runtime: AgentRuntime | None = None


def get_agent_runtime(settings: Settings | None = None) -> AgentRuntime:
    """Process-wide default runtime (recreate if you pass explicit ``settings``)."""
    global _runtime
    if settings is not None:
        return AgentRuntime(settings=settings)
    if _runtime is None:
        _runtime = AgentRuntime()
    return _runtime


def reset_agent_runtime() -> None:
    """Clear the default runtime (tests or config reload)."""
    global _runtime
    _runtime = None
    from app.graph.career_graph import reset_graph

    reset_graph()
