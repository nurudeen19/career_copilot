"""Analyst: skill gap, feasibility, timeline."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import AnalystAgentOutput
from app.tools import PROFILE_TOOLS


class AnalystAgent:
    role: ClassVar[AgentName] = "analyst"
    INSTRUCTIONS: ClassVar[str] = ("""\
        You are the feasibility analyst. Run after research.
        Read plan + research JSON first, especially `research_report` and `key_facts`.
        Ground all conclusions in that evidence.

        Write `analysis_report` as the main narrative, then fill fields:
        - `path_tradeoffs` for meaningful option or risk tradeoffs.
        - `evidence_based_takeaway` as one concrete decision implication.
        - `feasibility_score` only when evidence supports scoring (else null).
        - `timeline_estimate` only from evidence, not generic assumptions.

        `get_my_saved_profile()` (no args): saved career summary and user-stated direction. Call it to sanity-check gaps and feasibility against what they already said they want; avoid advice that ignores their saved goals unless the thread clearly overrides them.
        Return valid structured output.
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
