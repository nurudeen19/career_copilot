"""Environment-backed settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.agents import AgentsConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Career Copilot"
    debug: bool = False

    database_url: str | None = Field(
        default=None,
        description="SQLAlchemy URL, e.g. postgresql+psycopg://user:pass@localhost:5432/career_copilot",
    )
    jwt_secret: str = Field(default="change-me", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    openai_api_key: str | None = None
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    google_api_key: str | None = None
    tavily_api_key: str | None = None
    brave_search_api_key: str | None = None

    # LangSmith / LangChain tracing (optional)
    langchain_tracing_v2: bool = Field(default=False, description="Set LANGCHAIN_TRACING_V2 for LangSmith runs.")
    langchain_api_key: str | None = Field(
        default=None,
        description="LangSmith API key (also sets LANGCHAIN_API_KEY when tracing is on).",
    )
    langchain_project: str | None = Field(default="career-copilot", description="LANGCHAIN_PROJECT for traces.")

    max_user_input_chars: int = 1_000
    max_user_estimated_tokens: int = 800
    graph_checkpoint_sqlite_path: str = ".data/langgraph_checkpoints.sqlite"

    huggingface_token: str | None = Field(
        default=None,
        description="Hugging Face token (Llama Prompt Guard 2). If unset, HF_TOKEN / HUGGING_FACE_HUB_TOKEN env is used.",
    )
    prompt_guard_model_id: str = Field(
        default="meta-llama/Llama-Prompt-Guard-2-86M",
        description="HF model id for user-input prompt-injection classification.",
    )
    prompt_guard_device: int = Field(
        default=-1,
        description="Transformers pipeline device: -1 CPU, 0+ CUDA index.",
    )

    agents: AgentsConfig = Field(default_factory=AgentsConfig)


@lru_cache
def get_settings() -> Settings:
    return Settings()
