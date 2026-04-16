"""Critic: challenge timelines, constraints, assumptions."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime


class CriticAgent:
    role: ClassVar[AgentName] = "critic"
    INSTRUCTIONS: ClassVar[str] = (
        "You are a skeptical reviewer of career plans. Challenge optimistic timelines, "
        "surface missing constraints, and flag risky assumptions. Prefer concise, actionable concerns."
    )
    TOOLS: ClassVar[tuple[Any, ...]] = ()
    RESPONSE_FORMAT: ClassVar[Any | None] = None

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
