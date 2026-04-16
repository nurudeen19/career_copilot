"""Planner: current state, target role, constraints."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime


class PlannerAgent:
    role: ClassVar[AgentName] = "planner"
    INSTRUCTIONS: ClassVar[str] = (
        "You are a career planning specialist. Given the user's situation and goals, "
        "extract structured information: current role or state, target role or direction, "
        "and constraints (time, budget, location). Output clear subtasks when helpful."
    )
    TOOLS: ClassVar[tuple[Any, ...]] = ()
    # Optional: set to a Pydantic model type, ToolStrategy, ProviderStrategy, etc. (see LangChain create_agent docs).
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
        user_message = context.get("user_message", "")
        return {
            "agent": "planner",
            "current_state": None,
            "target_role": None,
            "constraints": {"time": None, "money": None, "location": None},
            "subtasks": [],
            "notes": (
                "Stub: wire self.graph.invoke(...) with messages when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
            "raw_user_message": user_message,
        }
