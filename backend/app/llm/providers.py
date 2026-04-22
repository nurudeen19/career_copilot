"""Map ``AgentLLMConfig.model_provider`` to a LangChain chat model (optional ``with_fallbacks``)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.language_models.chat_models import BaseChatModel

from app.config.agents import AgentLLMConfig

if TYPE_CHECKING:
    from app.config.settings import Settings

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"


def _require_key(label: str, value: str | None) -> str:
    if value is None or not str(value).strip():
        raise ValueError(
            f"{label} is required for this agent's model_provider; set it in the environment or .env."
        )
    return str(value).strip()


def _instantiate_chat_model(agent_llm_config: AgentLLMConfig, settings: Settings) -> BaseChatModel:
    """Single provider/model instance (no fallback chain)."""
    provider = agent_llm_config.model_provider

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=agent_llm_config.model,
            temperature=agent_llm_config.temperature,
            max_tokens=agent_llm_config.max_tokens,
            api_key=_require_key("OPENAI_API_KEY", settings.agents.openai_api_key),
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=agent_llm_config.model,
            temperature=agent_llm_config.temperature,
            max_tokens=agent_llm_config.max_tokens,
            api_key=_require_key("GROQ_API_KEY", settings.agents.groq_api_key),
        )

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=agent_llm_config.model,
            temperature=agent_llm_config.temperature,
            max_tokens=agent_llm_config.max_tokens,
            api_key=_require_key("OPENROUTER_API_KEY", settings.agents.openrouter_api_key),
            base_url=OPENROUTER_API_BASE,
        )

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=agent_llm_config.model,
            temperature=agent_llm_config.temperature,
            max_output_tokens=agent_llm_config.max_tokens,
            google_api_key=_require_key("GOOGLE_API_KEY", settings.agents.google_api_key),
        )

    raise ValueError(f"Unsupported model_provider: {provider!r}")


def build_chat_model(agent_llm_config: AgentLLMConfig, settings: Settings) -> Any:
    """
    Build a chat model for ``create_agent``.

    When ``fallback_model`` and ``fallback_model_provider`` are set, returns
    ``primary.with_fallbacks([secondary])`` (a ``RunnableWithFallbacks``). ``AgentRuntime``
    passes that runnable through to ``create_agent`` for structured agents so LangChain can
    invoke the backup on primary failure.
    """
    primary = _instantiate_chat_model(agent_llm_config, settings)
    fb_model = (agent_llm_config.fallback_model or "").strip()
    fb_prov = agent_llm_config.fallback_model_provider
    if not fb_model or fb_prov is None:
        return primary

    fb_cfg = agent_llm_config.model_copy(
        update={
            "model": fb_model,
            "model_provider": fb_prov,
            "fallback_model": None,
            "fallback_model_provider": None,
        }
    )
    secondary = _instantiate_chat_model(fb_cfg, settings)
    return primary.with_fallbacks([secondary])
