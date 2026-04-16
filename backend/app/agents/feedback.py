"""Feedback analyzer: thumbs-down and follow-ups → adaptation hints."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime


class FeedbackAgent:
    role: ClassVar[AgentName] = "feedback"
    INSTRUCTIONS: ClassVar[str] = (
        "You interpret user dissatisfaction and follow-up corrections. "
        "Produce adaptation hints the system can use to adjust tone, depth, or focus on the next turn."
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
