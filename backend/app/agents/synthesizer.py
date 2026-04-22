"""Synthesizer: recommendation, roadmap, risks."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import SynthesizerAgentOutput
from app.tools import PROFILE_TOOLS


class SynthesizerAgent:
    role: ClassVar[AgentName] = "synthesizer"
    INSTRUCTIONS: ClassVar[str] = ("""\
        You are the synthesizer. You are the final stage before the user sees the answer.
        The system JSON includes the plan, research, analysis, and critique. Read all four before writing. Your output must integrate all of them — do not favor one source and neglect others.

        Ground recommendation and key_insights directly in research.research_report and research.key_facts. Do not give advice that could apply without those specific findings. Fill comparison_verdict when the user compared options. Fill immediate_next_steps with concrete short-horizon actions. roadmap must be ordered phases over time, not a flat list. 
        limitations_acknowledged must briefly state the unresolved open_questions from research and the major concerns raised by the critic that the evidence does not fully resolve — do not silently dismiss them.

        If the user is authenticated, call get_my_saved_profile() to ensure the recommendation aligns with their saved goals, stack, salary expectations, and relocation preferences.
        Do not invent tool results or fabricate sources. Your final reply must match the structured output schema.
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
