"""Critic: challenge timelines, constraints, assumptions."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import CriticAgentOutput
from app.tools import PROFILE_TOOLS


class CriticAgent:
    role: ClassVar[AgentName] = "critic"
    INSTRUCTIONS: ClassVar[str] = ("""\
        You are the skeptical reviewer. Run after analyst with plan/research/analysis JSON.
        Stress-test analysis against the evidence.

        Write `critique_report` first:
        - call out over-claims or weak support,
        - explicitly cover unresolved `research.open_questions`.
        Then fill `concerns`, `missing_constraints`, `risky_assumptions`, and
        `decision_blind_spots` with specific, non-duplicative bullets.

        `get_my_saved_profile()` (no args): saved career summary and goals. Use it to flag whether analysis ignored known user constraints or stated direction.
        Return valid structured output.
    """)
    TOOLS: ClassVar[tuple[Any, ...]] = PROFILE_TOOLS
    RESPONSE_FORMAT: ClassVar[Any | None] = CriticAgentOutput

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
        analysis = context.get("analysis") or {}
        return {
            "agent": "critic",
            "critique_report": "",
            "decision_blind_spots": [],
            "concerns": [],
            "missing_constraints": [],
            "risky_assumptions": [],
            "notes": (
                "Stub: invoke self.graph with analysis + prior context when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
            "analysis_keys": list(analysis.keys()),
        }
