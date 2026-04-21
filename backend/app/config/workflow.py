"""LangGraph / user-input bounds (env: ``WORKFLOW__*`` nested under ``Settings.workflow``)."""

from pydantic import BaseModel, ConfigDict, Field


class WorkflowSettings(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    max_user_input_chars: int = Field(default=1_000, ge=1)
    max_user_estimated_tokens: int = Field(default=800, ge=1)
    graph_checkpoint_sqlite_path: str = Field(default=".data/langgraph_checkpoints.sqlite")
