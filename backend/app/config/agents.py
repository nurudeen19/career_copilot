"""LLM provider keys + per-agent model config. Keys: ``OPENAI_API_KEY``, … or ``AGENTS__<role>__*``."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AgentName = Literal["planner", "research", "analyst", "critic", "synthesizer", "feedback"]
ModelProvider = Literal["openai", "groq", "openrouter", "google"]


class AgentLLMConfig(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    model: str = Field(default="gpt-4o-mini")
    model_provider: ModelProvider = Field(default="openai")
    fallback_model: str | None = None
    fallback_model_provider: ModelProvider | None = None

    @field_validator("model_provider", mode="before")
    @classmethod
    def normalize_model_provider(cls, value: object) -> ModelProvider:
        if not isinstance(value, str):
            raise TypeError("model_provider must be a string")
        normalized = value.strip().lower()
        allowed: tuple[ModelProvider, ...] = ("openai", "groq", "openrouter", "google")
        if normalized not in allowed:
            raise ValueError(f"model_provider must be one of {allowed}, got {value!r}")
        return normalized  # type: ignore[return-value]

    @field_validator("fallback_model_provider", mode="before")
    @classmethod
    def normalize_fallback_model_provider(cls, value: object) -> ModelProvider | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if not isinstance(value, str):
            raise TypeError("fallback_model_provider must be a string or empty")
        normalized = value.strip().lower()
        allowed: tuple[ModelProvider, ...] = ("openai", "groq", "openrouter", "google")
        if normalized not in allowed:
            raise ValueError(f"fallback_model_provider must be one of {allowed}, got {value!r}")
        return normalized  # type: ignore[return-value]

    @model_validator(mode="after")
    def fallback_pair(self) -> AgentLLMConfig:
        a, b = self.fallback_model, self.fallback_model_provider
        if (a is None or not str(a).strip()) and b is None:
            return self
        if (a is None or not str(a).strip()) or b is None:
            raise ValueError("fallback_model and fallback_model_provider must both be set or both omitted")
        if str(a).strip() == self.model.strip() and b == self.model_provider:
            raise ValueError("fallback_model must differ from the primary model (or use a different provider)")
        return self


class AgentsConfig(BaseModel):
    """Provider keys and each agent's model block."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    openai_api_key: str | None = None
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    google_api_key: str | None = None
    tavily_api_key: str | None = None
    brave_search_api_key: str | None = None

    planner: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    research: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    analyst: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    critic: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    synthesizer: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    feedback: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
