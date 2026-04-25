"""Synthesizer: recommendation, roadmap, risks."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import SynthesizerAgentOutput
from app.tools import PROFILE_TOOLS


class SynthesizerAgent:
    role: ClassVar[AgentName] = "synthesizer"
    INSTRUCTIONS: ClassVar[str] = ("""\
        You are the final synthesizer before user output.
        Read plan, research, analysis, and critique JSON and integrate all of them.

        Requirements:
        - Ground `recommendation` and `key_insights` in research evidence.
        - Fill `comparison_verdict` when options are being compared.
        - Keep `immediate_next_steps` concrete and near-term.
        - Keep `roadmap` as ordered phases.
        - In `limitations_acknowledged`, state unresolved open questions and major critic concerns.
        - Do not invent tool results or sources.

        If authenticated, call `get_my_saved_profile()` when it improves alignment.
        Return valid structured output.
    """)
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
            "comparison_verdict": "",
            "key_insights": [],
            "roadmap": [],
            "immediate_next_steps": [],
            "risks": [],
            "limitations_acknowledged": "",
            "notes": (
                "Stub: invoke self.graph with full pipeline context when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
        }
