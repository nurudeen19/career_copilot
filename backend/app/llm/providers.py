"""Map ``AgentLLMConfig.model_provider`` to a LangChain chat model (one function, no caches)."""

from __future__ import annotations

from typing import TYPE_CHECKING

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


def build_chat_model(agent_llm_config: AgentLLMConfig, settings: Settings) -> BaseChatModel:
    """Build a ``BaseChatModel`` for the configured provider."""
    provider = agent_llm_config.model_provider

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=agent_llm_config.model,
            temperature=agent_llm_config.temperature,
            max_tokens=agent_llm_config.max_tokens,
            api_key=_require_key("OPENAI_API_KEY", settings.openai_api_key),
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=agent_llm_config.model,
            temperature=agent_llm_config.temperature,
            max_tokens=agent_llm_config.max_tokens,
            api_key=_require_key("GROQ_API_KEY", settings.groq_api_key),
        )

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=agent_llm_config.model,
            temperature=agent_llm_config.temperature,
            max_tokens=agent_llm_config.max_tokens,
            api_key=_require_key("OPENROUTER_API_KEY", settings.openrouter_api_key),
            base_url=OPENROUTER_API_BASE,
        )

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=agent_llm_config.model,
            temperature=agent_llm_config.temperature,
            max_output_tokens=agent_llm_config.max_tokens,
            google_api_key=_require_key("GOOGLE_API_KEY", settings.google_api_key),
        )

    raise ValueError(f"Unsupported model_provider: {provider!r}")
