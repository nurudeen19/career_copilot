"""Synthesizer: recommendation, roadmap, risks."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime


class SynthesizerAgent:
    role: ClassVar[AgentName] = "synthesizer"
    INSTRUCTIONS: ClassVar[str] = (
        "You are a career copilot synthesizer. Merge planner, research, analyst, and critic "
        "outputs into a clear recommendation, phased roadmap, and honest risk list for the user."
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
        return {
            "agent": "synthesizer",
            "recommendation": None,
            "roadmap": [],
            "risks": [],
            "notes": (
                "Stub: invoke self.graph with full pipeline context when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
        }
