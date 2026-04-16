"""Per-agent LLM parameters (temperature, caps, model, provider)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AgentName = Literal["planner", "research", "analyst", "critic", "synthesizer", "feedback"]

ModelProvider = Literal["openai", "groq", "openrouter", "google"]


class AgentLLMConfig(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    model: str = Field(default="gpt-4o-mini")
    model_provider: ModelProvider = Field(default="openai")

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


class AgentsConfig(BaseModel):
    """One block of LLM settings per agent (override via env on parent Settings)."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    planner: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    research: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    analyst: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    critic: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    synthesizer: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
    feedback: AgentLLMConfig = Field(default_factory=AgentLLMConfig)
