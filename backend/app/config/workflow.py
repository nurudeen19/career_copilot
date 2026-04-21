"""LangGraph / user-input bounds (mixed into ``Settings``)."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class WorkflowSettings(BaseModel):
    """``MAX_USER_INPUT_CHARS``, ``GRAPH_CHECKPOINT_SQLITE_PATH``, …"""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    max_user_input_chars: int = Field(
        default=1_000,
        ge=1,
        validation_alias=AliasChoices("MAX_USER_INPUT_CHARS"),
    )
    max_user_estimated_tokens: int = Field(
        default=800,
        ge=1,
        validation_alias=AliasChoices("MAX_USER_ESTIMATED_TOKENS"),
    )
    graph_checkpoint_sqlite_path: str = Field(
        default=".data/langgraph_checkpoints.sqlite",
        validation_alias=AliasChoices("GRAPH_CHECKPOINT_SQLITE_PATH"),
    )
    llm_history_max_tokens: int = Field(
        default=5_000,
        ge=512,
        description="Approximate token cap for **planner + feedback** chat history only (checkpoint unchanged).",
        validation_alias=AliasChoices("LLM_HISTORY_MAX_TOKENS"),
    )
