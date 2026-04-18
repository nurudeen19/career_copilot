"""Critic: challenge timelines, constraints, assumptions."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import CriticAgentOutput
from app.tools import PROFILE_TOOLS


class CriticAgent:
    role: ClassVar[AgentName] = "critic"
    INSTRUCTIONS: ClassVar[str] = (
        "You are the skeptical reviewer (after analyst). System context includes plan, research, and analysis. "
        "Optionally call get_my_saved_profile (no arguments) to check constraints vs profile. "
        "List concerns, missing_constraints, risky_assumptions — short and actionable. "
        "Your final reply MUST match the structured output schema."
    )
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
            "concerns": [],
            "missing_constraints": [],
            "risky_assumptions": [],
            "notes": (
                "Stub: invoke self.graph with analysis + prior context when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
            "analysis_keys": list(analysis.keys()),
        }
