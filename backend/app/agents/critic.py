"""Critic: challenge timelines, constraints, assumptions."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import CriticAgentOutput
from app.tools import PROFILE_TOOLS


class CriticAgent:
    role: ClassVar[AgentName] = "critic"
    INSTRUCTIONS: ClassVar[str] = ("""\
        You are the skeptical reviewer (after analyst). System context includes plan, research, and analysis JSON.
        before writing anything. Your job is to stress-test the analysis against the evidence, critique_report must assess whether the analysis over-claims relative to what the research actually supports, and explicitly address any unresolved research.open_questions the analyst ignored. Write this as a coherent narrative first.

        Use concerns, missing_constraints, and risky_assumptions as sharp, specific bullets that complement critique_report — not restatements of it. Populate decision_blind_spots with what the user is likely to overlook or underweight when making their decision.

        If the user is authenticated, call get_my_saved_profile() to check whether known constraints or goals were ignored in the analysis.
        Your final reply must match the structured output schema.
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
