"""Agent LLM blocks, provider keys, and :class:`AgentsConfig` (mixed into ``Settings`` — no duplicate mapping)."""

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
    """API keys + per-role ``PLANNER_*`` / ``RESEARCH_*`` env fields; role blocks are properties."""

    model_config = ConfigDict(extra="ignore")

    openai_api_key: str | None = None
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    google_api_key: str | None = None
    tavily_api_key: str | None = None
    brave_search_api_key: str | None = None

    planner_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    planner_max_tokens: int = Field(default=4096, ge=1)
    planner_model: str = Field(default="gpt-4o-mini")
    planner_model_provider: ModelProvider = Field(default="openai")
    planner_fallback_model: str | None = None
    planner_fallback_model_provider: ModelProvider | None = None

    research_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    research_max_tokens: int = Field(default=4096, ge=1)
    research_model: str = Field(default="gpt-4o-mini")
    research_model_provider: ModelProvider = Field(default="openai")
    research_fallback_model: str | None = None
    research_fallback_model_provider: ModelProvider | None = None

    analyst_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    analyst_max_tokens: int = Field(default=4096, ge=1)
    analyst_model: str = Field(default="gpt-4o-mini")
    analyst_model_provider: ModelProvider = Field(default="openai")
    analyst_fallback_model: str | None = None
    analyst_fallback_model_provider: ModelProvider | None = None

    critic_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    critic_max_tokens: int = Field(default=4096, ge=1)
    critic_model: str = Field(default="gpt-4o-mini")
    critic_model_provider: ModelProvider = Field(default="openai")
    critic_fallback_model: str | None = None
    critic_fallback_model_provider: ModelProvider | None = None

    synthesizer_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    synthesizer_max_tokens: int = Field(default=4096, ge=1)
    synthesizer_model: str = Field(default="gpt-4o-mini")
    synthesizer_model_provider: ModelProvider = Field(default="openai")
    synthesizer_fallback_model: str | None = None
    synthesizer_fallback_model_provider: ModelProvider | None = None

    feedback_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    feedback_max_tokens: int = Field(default=4096, ge=1)
    feedback_model: str = Field(default="gpt-4o-mini")
    feedback_model_provider: ModelProvider = Field(default="openai")
    feedback_fallback_model: str | None = None
    feedback_fallback_model_provider: ModelProvider | None = None

    def _llm(self, role: AgentName) -> AgentLLMConfig:
        return AgentLLMConfig(
            temperature=getattr(self, f"{role}_temperature"),
            max_tokens=getattr(self, f"{role}_max_tokens"),
            model=getattr(self, f"{role}_model"),
            model_provider=getattr(self, f"{role}_model_provider"),
            fallback_model=getattr(self, f"{role}_fallback_model"),
            fallback_model_provider=getattr(self, f"{role}_fallback_model_provider"),
        )

    @property
    def planner(self) -> AgentLLMConfig:
        return self._llm("planner")

    @property
    def research(self) -> AgentLLMConfig:
        return self._llm("research")

    @property
    def analyst(self) -> AgentLLMConfig:
        return self._llm("analyst")

    @property
    def critic(self) -> AgentLLMConfig:
        return self._llm("critic")

    @property
    def synthesizer(self) -> AgentLLMConfig:
        return self._llm("synthesizer")

    @property
    def feedback(self) -> AgentLLMConfig:
        return self._llm("feedback")
