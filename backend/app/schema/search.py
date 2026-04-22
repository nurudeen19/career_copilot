"""Uniform shape for web search tool results (Tavily + Brave)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    """One search result, normalized for agents."""

    rank: int = Field(..., ge=1, description="Order in this response (1-based).")
    title: str = Field(..., description="Result title.")
    url: str = Field(..., description="Canonical result URL.")
    summary: str = Field(
        ...,
        description="Rich text for the model: snippets, extra passages, or extracted page text.",
    )
    source: Literal["tavily", "brave"] = Field(..., description="Which search backend produced this hit.")
    relevance_score: float | None = Field(
        default=None,
        description="Backend relevance score when provided (e.g. Tavily score).",
    )
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional provider fields (page_age, language, favicon URL, etc.).",
    )


class SearchToolResponse(BaseModel):
    """What search tools return to the agent (JSON string in practice)."""

    provider: Literal["tavily", "brave"]
    query: str
    overview: str | None = Field(
        default=None,
        description="Short synthesis when the backend provides one (e.g. Tavily answer).",
    )
    hits: list[SearchHit] = Field(default_factory=list)
    error: str | None = Field(default=None, description="Set when the search could not complete usefully.")

    def to_agent_text(self) -> str:
        """Stable, readable JSON for LLM consumption."""
        return self.model_dump_json(indent=2)
