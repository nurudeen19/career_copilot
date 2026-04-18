"""Synthesizer: recommendation, roadmap, risks."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import SynthesizerAgentOutput
from app.tools import PROFILE_TOOLS


class SynthesizerAgent:
    role: ClassVar[AgentName] = "synthesizer"
    INSTRUCTIONS: ClassVar[str] = (
        "You are the synthesizer (final stage before the user sees the answer). "
        "System context carries plan, research, analysis, and critique — merge into recommendation, roadmap phases, and risks. "
        "Optionally call get_user_profile_by_id when UUID is present so advice matches profile (goals, stack, relocation, salary). "
        "Do not invent tool results. Your final reply MUST match the structured output schema."
    )
    TOOLS: ClassVar[tuple[Any, ...]] = PROFILE_TOOLS
    RESPONSE_FORMAT: ClassVar[Any | None] = SynthesizerAgentOutput

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
