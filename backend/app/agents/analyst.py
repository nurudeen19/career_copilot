"""Analyst: skill gap, feasibility, timeline."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import AnalystAgentOutput
from app.tools import PROFILE_TOOLS


class AnalystAgent:
    role: ClassVar[AgentName] = "analyst"
    INSTRUCTIONS: ClassVar[str] = ("""\
        You are the feasibility analyst. You run after research.
        The system JSON includes the plan and research output. Read research.research_report and research.key_facts first — they carry the substantive findings. Ground everything you write in that evidence.

        Write analysis_report as a coherent narrative before populating structured fields. Fill skill_gaps and scores only after the narrative is solid. Populate path_tradeoffs when multiple paths exist or when a single path carries meaningful risk. evidence_based_takeaway must be one paragraph summarizing the implication for the user's specific decision — not generic advice.
        
        Set feasibility_score (1–10) only when evidence supports it; otherwise leave null. timeline_estimate must reflect research findings, not generic assumptions.

        If the user is authenticated, call get_my_saved_profile() to validate against their saved goals and salary expectations. Your final reply must match the structured output schema.
    """)
    TOOLS: ClassVar[tuple[Any, ...]] = PROFILE_TOOLS
    RESPONSE_FORMAT: ClassVar[Any | None] = AnalystAgentOutput

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime

    @property
    def graph(self) -> Any:
        return self._runtime.initialize_agent(
            self.role,
            instructions=self.INSTRUCTIONS,
            tools=self.TOOLS,
            response_format=self.RESPONSE_FORMAT,
        )

    def run(self, context: dict) -> dict:
        agent_llm_config = getattr(self._runtime.settings.agents, self.role)
        plan = context.get("plan") or {}
        research = context.get("research") or {}
        return {
            "agent": "analyst",
            "analysis_report": "",
            "path_tradeoffs": [],
            "evidence_based_takeaway": "",
            "skill_gaps": [],
            "feasibility_score": None,
            "timeline_estimate": None,
            "notes": (
                "Stub: invoke self.graph with plan + research context when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
            "inputs_summary": {"plan_keys": list(plan.keys()), "research_keys": list(research.keys())},
        }
