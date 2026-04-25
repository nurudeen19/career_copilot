"""Structured final responses per agent (LangChain ``response_format``)."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator


class PlannerConstraints(BaseModel):
    time: str | None = Field(default=None, description="Time constraints.")
    money: str | None = Field(default=None, description="Budget constraints.")
    location: str | None = Field(default=None, description="Location constraints.")


class PlannerAgentOutput(BaseModel):
    """Planner routing + minimal planning context."""

    current_state: str | None = Field(default=None, description="User's current situation.")
    target_role: str | None = Field(default=None, description="User's target role/path.")
    decision_question: str | None = Field(
        default=None,
        description="Concrete career decision to answer.",
    )
    options_being_considered: list[str] = Field(
        default_factory=list,
        description="Options to compare, if any.",
    )
    constraints: PlannerConstraints = Field(default_factory=PlannerConstraints)
    subtasks: list[str] = Field(
        default_factory=list,
        description="Research questions to resolve.",
    )
    notes: str = Field(default="", description="Short planning notes.")
    handoff: Literal["research", "user_clarify", "user_casual_redirect"] = Field(
        ...,
        description="Required routing decision.",
    )
    assistant_message: str | None = Field(
        default=None,
        description="User-visible message for non-research handoffs.",
    )

    @model_validator(mode="after")
    def normalize_assistant_message(self) -> Self:
        """Keep planner handoffs safe for graph user output."""
        msg = (self.assistant_message or "").strip()
        if self.handoff == "research":
            self.assistant_message = msg or None
            return self
        if msg:
            self.assistant_message = msg
            return self
        if self.handoff == "user_casual_redirect":
            self.assistant_message = "Happy to help. What career question should we work on?"
            return self
        self.assistant_message = "Could you share a bit more about your career goal so I can help?"
        return self


class ResearchSourceRef(BaseModel):
    title: str | None = None
    url: str | None = None
    note: str | None = None


class ResearchAgentOutput(BaseModel):
    """Research evidence for downstream decision-making."""

    research_report: str = Field(
        ...,
        description="Primary findings narrative.",
    )
    topics_addressed: list[str] = Field(
        default_factory=list,
        description="Themes covered.",
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="Skills supported by evidence.",
    )
    salary_benchmarks: dict[str, Any] = Field(
        default_factory=dict,
        description="Comp data when available.",
    )
    market_demand: dict[str, Any] = Field(
        default_factory=dict,
        description="Demand data when available.",
    )
    key_facts: list[str] = Field(
        default_factory=list,
        description="Critical factual points.",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Unknowns and missing info.",
    )
    comparison_summary: str = Field(
        default="",
        description="Comparison summary, if applicable.",
    )
    evidence_based_next_steps: list[str] = Field(
        default_factory=list,
        description="Concrete evidence-backed next steps.",
    )
    sources: list[ResearchSourceRef] = Field(default_factory=list, description="Source references.")
    research_method_notes: str = Field(
        default="",
        description="Brief methods and confidence notes.",
    )


class AnalystAgentOutput(BaseModel):
    """Feasibility and tradeoff analysis."""

    analysis_report: str = Field(
        default="",
        description="Main analysis narrative.",
    )
    path_tradeoffs: list[str] = Field(
        default_factory=list,
        description="Option tradeoffs or key risks.",
    )
    evidence_based_takeaway: str = Field(
        default="",
        description="Decision implication from evidence.",
    )
    skill_gaps: list[str] = Field(default_factory=list)
    feasibility_score: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="1-10 feasibility, or null.",
    )
    timeline_estimate: str | None = Field(default=None, description="Estimated timeline.")
    notes: str = Field(default="", description="Short analysis notes.")


class CriticAgentOutput(BaseModel):
    """Critical review of analysis quality."""

    critique_report: str = Field(
        default="",
        description="Main critique narrative.",
    )
    decision_blind_spots: list[str] = Field(
        default_factory=list,
        description="Likely user blind spots.",
    )
    concerns: list[str] = Field(default_factory=list)
    missing_constraints: list[str] = Field(default_factory=list)
    risky_assumptions: list[str] = Field(default_factory=list)
    notes: str = Field(default="", description="Short critique notes.")


class RoadmapPhase(BaseModel):
    phase: str = Field(description="Roadmap phase label.")
    actions: list[str] = Field(
        default_factory=list,
        description="Actions for this phase.",
    )


class SynthesizerAgentOutput(BaseModel):
    """Final user-facing recommendation package."""

    recommendation: str = Field(
        default="",
        description="Primary recommendation.",
    )
    comparison_verdict: str = Field(
        default="",
        description="Verdict for compared options.",
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="Key evidence-backed insights.",
    )
    roadmap: list[RoadmapPhase] = Field(
        default_factory=list,
        description="Ordered action phases.",
    )
    immediate_next_steps: list[str] = Field(
        default_factory=list,
        description="Near-term concrete actions.",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Risks and downside scenarios.",
    )
    limitations_acknowledged: str = Field(
        default="",
        description="Known limitations and uncertainties.",
    )
    notes: str = Field(default="", description="Optional final notes.")
