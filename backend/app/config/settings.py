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
    log_level: str = Field(
        default="INFO",
        description="Root log level: DEBUG, INFO, WARNING, ERROR (also applied to uvicorn loggers).",
    )
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated origins for browser clients; use * to allow any (no credentials).",
    )

    database_url: str | None = Field(
        default=None,
        description="SQLAlchemy URL, e.g. postgresql+psycopg://user:pass@localhost:5432/career_copilot",
    )
    jwt_secret: str = Field(default="change-me", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    public_app_base_url: str = Field(
        default="http://127.0.0.1:8000",
        description="Public API base URL (no trailing slash) for auth links in outbound email.",
    )

    mailtrap_api_token: str | None = Field(
        default=None,
        description="Mailtrap Sending API token (Bearer) for live transactional delivery.",
    )
    mail_from_email: str = Field(
        default="noreply@example.com",
        description="From address for transactional email (must be allowed in Mailtrap / your domain).",
    )
    mail_from_name: str = Field(default="Career Copilot", description="Display name for the From header.")

    auth_dev_auto_verify_email: bool = Field(
        default=False,
        description="If true, skip Mailtrap on register and mark email verified (tests/local only).",
    )

    rate_limit_enabled: bool = Field(
        default=True,
        description="When false, SlowAPI limits are effectively disabled (very high ceilings).",
    )
    rate_limit_login: str = Field(default="20/minute", description="Limit string for POST /auth/login.")
    rate_limit_register: str = Field(default="10/minute", description="Limit for POST /auth/register.")
    rate_limit_auth_email: str = Field(
        default="8/minute",
        description="Limit for POST /auth/resend-verification and /auth/forgot-password.",
    )
    rate_limit_verify_email_get: str = Field(default="45/minute", description="Limit for GET /auth/verify-email.")
    rate_limit_reset_password: str = Field(
        default="15/minute",
        description="Limit for POST /auth/reset-password and GET reset form.",
    )
    rate_limit_profile: str = Field(default="120/minute", description="Limit for GET/PATCH /profile.")
    rate_limit_workflow_stream: str = Field(default="24/minute", description="Limit for POST /workflow/stream.")
    rate_limit_health: str = Field(default="120/minute", description="Limit for GET /health.")

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
        description="LangSmith API key; copied to LANGCHAIN_API_KEY at startup (langsmith also accepts LANGSMITH_API_KEY in the process env).",
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
