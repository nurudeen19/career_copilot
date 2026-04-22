"""Structured final responses per agent (LangChain ``response_format``)."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator


class PlannerConstraints(BaseModel):
    time: str | None = Field(default=None, description="Time or schedule constraints.")
    money: str | None = Field(default=None, description="Budget or compensation constraints.")
    location: str | None = Field(default=None, description="Location or mobility constraints.")


class PlannerAgentOutput(BaseModel):
    """Planner: frame the career decision / switch so research and synthesis stay decision-relevant."""

    current_state: str | None = Field(default=None, description="Where the user is today (role, level, context).")
    target_role: str | None = Field(default=None, description="Where they want to go (role, domain, seniority).")
    decision_question: str | None = Field(
        default=None,
        description=(
            "One sentence: the concrete decision, transition, or comparison advice is for "
            "(e.g. 'IC vs EM', 'leave FAANG for startup', 'which stack to bet on'). Drives research scope."
        ),
    )
    options_being_considered: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit paths, roles, or employer types to contrast when the user is choosing among options; "
            "empty if a single direction or exploratory growth (not a comparison)."
        ),
    )
    constraints: PlannerConstraints = Field(default_factory=PlannerConstraints)
    subtasks: list[str] = Field(
        default_factory=list,
        description="Research-sized questions that must be answered for the user to decide (evidence targets).",
    )
    notes: str = Field(default="", description="Short planner commentary or caveats.")
    handoff: Literal["research", "user_clarify", "user_casual_redirect"] = Field(
        default="research",
        description="research only with a clear career topic; user_clarify when unclear; "
        "user_casual_redirect for greetings, thanks, or non-career chat — steer toward a career question.",
    )
    assistant_message: str | None = Field(
        default=None,
        description="When handoff is not research, the user-facing reply (questions or redirect).",
    )

    @model_validator(mode="after")
    def coerce_research_without_career_topic(self) -> Self:
        """Avoid sending empty goals into the research pipeline."""
        if self.handoff != "research":
            return self
        if (
            (self.target_role or "").strip()
            or (self.current_state or "").strip()
            or self.subtasks
            or (self.decision_question or "").strip()
            or self.options_being_considered
        ):
            return self
        return self.model_copy(
            update={
                "handoff": "user_clarify",
                "assistant_message": (
                    "What career move should we dig into? For example: switching roles, getting promoted, "
                    "or breaking into a field—one sentence is enough to pull useful market research."
                ),
            }
        )

    @model_validator(mode="after")
    def compose_assistant_message_from_planner_fields(self) -> Self:
        """Never rely on graph-level static copy: derive missing user text only from planner fields."""
        if self.handoff == "research":
            return self
        if (self.assistant_message or "").strip():
            self.assistant_message = (self.assistant_message or "").strip()
            return self
        chunks: list[str] = []
        if self.current_state:
            chunks.append(str(self.current_state).strip())
        if self.target_role:
            chunks.append(str(self.target_role).strip())
        if (self.decision_question or "").strip():
            chunks.append(str(self.decision_question).strip())
        if self.options_being_considered:
            opts = [str(o).strip() for o in self.options_being_considered if str(o).strip()]
            if opts:
                chunks.append("Options to compare:\n" + "\n".join(f"- {o}" for o in opts))
        c = self.constraints.model_dump(exclude_none=True)
        if c:
            parts = [f"{k}: {v}" for k, v in c.items()]
            chunks.append("Constraints — " + "; ".join(parts))
        if self.subtasks:
            chunks.append("Here are some focused questions:\n" + "\n".join(f"- {s}" for s in self.subtasks))
        if self.notes:
            chunks.append(self.notes.strip())
        merged = "\n\n".join(x for x in chunks if x).strip()
        self.assistant_message = merged or None
        return self


class ResearchSourceRef(BaseModel):
    title: str | None = None
    url: str | None = None
    note: str | None = None


class ResearchAgentOutput(BaseModel):
    """Research-backed evidence so the user (via downstream agents) can decide, compare paths, and act."""

    research_report: str = Field(
        ...,
        description=(
            "Full findings: markdown or multi-paragraph plain text. Cover what matters for the user's decision "
            "(switch feasibility, role/market reality, tradeoffs, geographic or comp signals when relevant). "
            "Do not bury decision-critical detail only in optional dict fields."
        ),
    )
    topics_addressed: list[str] = Field(
        default_factory=list,
        description="Short labels for themes you investigated (e.g. 'IC vs manager path', 'EU hiring', 'stack depth').",
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="Skills to acquire or strengthen only when evidence supports; otherwise [].",
    )
    salary_benchmarks: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured comp signals only when the plan/thread calls for salary/comp — else {}.",
    )
    market_demand: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured hiring/demand signals only when you have that evidence — else {}.",
    )
    key_facts: list[str] = Field(
        default_factory=list,
        description="Atomic one-line factual claims later stages must not contradict (with nuance in report).",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Unknowns, unverified claims, or items needing user input — synthesizer must acknowledge these.",
    )
    comparison_summary: str = Field(
        default="",
        description=(
            "When plan.options_being_considered or decision_question implies a comparison/switch: "
            "evidence-weighted side-by-side (pros/cons per path, or 'single path' if not comparative). "
            "Otherwise a one-line 'N/A — single trajectory' is fine."
        ),
    )
    evidence_based_next_steps: list[str] = Field(
        default_factory=list,
        description=(
            "Prioritized concrete actions the user could take soon; each must be justified by the report or key_facts "
            "(not generic career boilerplate)."
        ),
    )
    sources: list[ResearchSourceRef] = Field(default_factory=list, description="Citations from search tools.")
    research_method_notes: str = Field(
        default="",
        description="Brief: queries/tools used and confidence; substantive findings belong in research_report.",
    )


class AnalystAgentOutput(BaseModel):
    """Analyst: feasibility and tradeoffs so the user can choose among paths with evidence."""

    analysis_report: str = Field(
        default="",
        description=(
            "Narrative synthesis: gaps, feasibility, timeline, and implications for the user's decision — "
            "grounded in research.research_report, comparison_summary, and key_facts."
        ),
    )
    path_tradeoffs: list[str] = Field(
        default_factory=list,
        description=(
            "Bullets comparing options or framing tradeoffs (e.g. stability vs upside); use when multiple paths exist, "
            "else bullets on single-path risks/opportunities."
        ),
    )
    evidence_based_takeaway: str = Field(
        default="",
        description=(
            "One tight paragraph: what the evidence implies for the user's next move (analysis layer only; "
            "synthesizer delivers final user-facing advice)."
        ),
    )
    skill_gaps: list[str] = Field(default_factory=list)
    feasibility_score: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="1–10 feasibility given evidence (null if insufficient data).",
    )
    timeline_estimate: str | None = Field(default=None, description="Human-readable timeline estimate.")
    notes: str = Field(default="", description="Structured bullets: tradeoffs, assumptions, missing data.")


class CriticAgentOutput(BaseModel):
    """Critic: stress-test whether advice would mislead the user's real decision."""

    critique_report: str = Field(
        default="",
        description=(
            "Short narrative: what is overstated, under-supported, or risky given research_report, "
            "comparison_summary, and analysis_report."
        ),
    )
    decision_blind_spots: list[str] = Field(
        default_factory=list,
        description=(
            "What the user might miss when choosing (stakes, reversibility, family/visa/geo, timing, optionality) "
            "— each bullet actionable."
        ),
    )
    concerns: list[str] = Field(default_factory=list)
    missing_constraints: list[str] = Field(default_factory=list)
    risky_assumptions: list[str] = Field(default_factory=list)
    notes: str = Field(default="", description="Concise actionable review (lists complement critique_report).")


class RoadmapPhase(BaseModel):
    phase: str = Field(description="Ordered chapter toward the user's goal (e.g. '0–30 days', 'Skill bridge').")
    actions: list[str] = Field(
        default_factory=list,
        description="Specific next steps for this phase — concrete enough to execute without another research pass.",
    )


class SynthesizerAgentOutput(BaseModel):
    """Synthesizer: researched-backed advice, comparisons, and next steps for the user's career decision."""

    recommendation: str = Field(
        default="",
        description=(
            "Bottom-line advice the user can act on: must reflect research_report, comparison paths, "
            "analysis, and critic — not generic career guidance."
        ),
    )
    comparison_verdict: str = Field(
        default="",
        description=(
            "When the user is choosing among paths: clear guidance (when to pick A vs B, or 'depends on X'). "
            "Empty if the thread was not comparative."
        ),
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="High-signal bullets the user should not miss (pulled from research_report / analysis / critic).",
    )
    roadmap: list[RoadmapPhase] = Field(
        default_factory=list,
        description="Ordered phases of next steps from near-term to longer horizon — aligned to evidence and constraints.",
    )
    immediate_next_steps: list[str] = Field(
        default_factory=list,
        description="3–7 concrete actions for the next days/weeks (before or alongside roadmap phases).",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Downside scenarios or deal-breakers the user should weigh against the recommendation.",
    )
    limitations_acknowledged: str = Field(
        default="",
        description=(
            "Explicit paragraph: open_questions, weak evidence, and critic flags you are not papering over "
            "in the user-facing recommendation."
        ),
    )
    notes: str = Field(default="", description="Tone, scope, or internal caveats for the user.")
