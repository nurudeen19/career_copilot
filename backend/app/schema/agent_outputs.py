"""Structured final responses per agent (LangChain ``response_format``)."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class PlannerConstraints(BaseModel):
    time: str | None = Field(default=None, description="Time or schedule constraints.")
    money: str | None = Field(default=None, description="Budget or compensation constraints.")
    location: str | None = Field(default=None, description="Location or mobility constraints.")


class PlannerAgentOutput(BaseModel):
    """Planner: situation → target path + constraints + routing for the LangGraph."""

    current_state: str | None = Field(default=None, description="Where the user is today (role, level, context).")
    target_role: str | None = Field(default=None, description="Where they want to go (role, domain, seniority).")
    constraints: PlannerConstraints = Field(default_factory=PlannerConstraints)
    subtasks: list[str] = Field(default_factory=list, description="Concrete follow-ups for research / user.")
    notes: str = Field(default="", description="Short planner commentary or caveats.")
    handoff: Literal["research", "user_clarify", "user_casual_redirect"] = Field(
        default="research",
        description="research: enough to run market research; user_clarify: ask the user; "
        "user_casual_redirect: off-topic — gently steer toward a career question.",
    )
    assistant_message: str | None = Field(
        default=None,
        description="When handoff is not research, the user-facing reply (questions or redirect).",
    )


class ResearchSourceRef(BaseModel):
    title: str | None = None
    url: str | None = None
    note: str | None = None


class ResearchAgentOutput(BaseModel):
    """Research: skills, compensation signals, demand — grounded in tools and profile when used."""

    required_skills: list[str] = Field(default_factory=list, description="Skills to acquire or strengthen.")
    salary_benchmarks: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured salary signals (ranges, labels, caveats).",
    )
    market_demand: dict[str, Any] = Field(
        default_factory=dict,
        description="Hiring/demand signals (roles, regions, trends).",
    )
    sources: list[ResearchSourceRef] = Field(default_factory=list, description="Citations from search tools.")
    notes: str = Field(default="", description="How research was done and what is still uncertain.")


class AnalystAgentOutput(BaseModel):
    """Analyst: gaps, feasibility, timeline from plan + research."""

    skill_gaps: list[str] = Field(default_factory=list)
    feasibility_score: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="1–10 feasibility given evidence (null if insufficient data).",
    )
    timeline_estimate: str | None = Field(default=None, description="Human-readable timeline estimate.")
    notes: str = Field(default="", description="Tradeoffs, assumptions, missing data.")


class CriticAgentOutput(BaseModel):
    """Critic: stress-test the analysis."""

    concerns: list[str] = Field(default_factory=list)
    missing_constraints: list[str] = Field(default_factory=list)
    risky_assumptions: list[str] = Field(default_factory=list)
    notes: str = Field(default="", description="Concise actionable review.")


class RoadmapPhase(BaseModel):
    phase: str = Field(description="Phase name or timeframe.")
    actions: list[str] = Field(default_factory=list, description="Concrete steps in this phase.")


class SynthesizerAgentOutput(BaseModel):
    """Synthesizer: user-facing recommendation and roadmap."""

    recommendation: str = Field(default="", description="Clear bottom-line advice.")
    roadmap: list[RoadmapPhase] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    notes: str = Field(default="", description="Tone, scope, or caveats for the user.")


class FeedbackAgentOutput(BaseModel):
    """Feedback: interpret dissatisfaction and suggest adjustments."""

    sentiment: str = Field(default="unknown", description="negative | neutral | positive | unknown")
    adaptation_hints: list[str] = Field(
        default_factory=list,
        description="Hints for the next turn (depth, tone, focus, missing checks).",
    )
    notes: str = Field(default="", description="Brief rationale.")
