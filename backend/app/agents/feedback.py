"""Feedback analyzer: thumbs-down and follow-ups → adaptation hints."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import FeedbackAgentOutput
from app.tools import PROFILE_TOOLS


class FeedbackAgent:
    role: ClassVar[AgentName] = "feedback"
    INSTRUCTIONS: ClassVar[str] = (
        "You run when the user rejects or dislikes a prior answer (before re-planning). "
        "Infer sentiment and produce adaptation_hints for the next planner pass (tone, depth, missing checks). "
        "Optionally call get_my_saved_profile (no arguments) if profile context helps. "
        "Your final reply MUST match the structured output schema."
    )
    TOOLS: ClassVar[tuple[Any, ...]] = PROFILE_TOOLS
    RESPONSE_FORMAT: ClassVar[Any | None] = FeedbackAgentOutput

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
        feedback = context.get("user_feedback")
        return {
            "agent": "feedback",
            "sentiment": "negative" if feedback == "down" else "unknown",
            "adaptation_hints": [],
            "notes": (
                "Stub: invoke self.graph with user_feedback and recent context when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
        }
