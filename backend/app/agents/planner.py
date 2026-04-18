"""Planner: current state, target role, constraints."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import PlannerAgentOutput
from app.tools import SEARCH_AND_PROFILE_TOOLS


class PlannerAgent:
    role: ClassVar[AgentName] = "planner"
    INSTRUCTIONS: ClassVar[str] = (
        "You are the career planner (first gate in the pipeline). "
        "Classify intent inside the structured fields — you do not need a separate classifier node. "
        "If the message is casual or off-topic, set handoff=user_casual_redirect and assistant_message to a short, "
        "friendly nudge toward a concrete career question. "
        "If you lack essentials (goal role, timeline, constraints), set handoff=user_clarify and assistant_message "
        "to specific questions (numbered bullets are fine). "
        "Only when you have enough to brief a researcher, set handoff=research and assistant_message may be null. "
        "Always fill current_state, target_role, constraints, subtasks, notes when handoff=research; for other handoffs "
        "those may be partial but still honest. "
        "When a user UUID is present, call get_user_profile_by_id first to align with saved profile fields. "
        "Use web search only to disambiguate vague job titles. "
        "Your final structured output MUST include handoff and assistant_message."
    )
    TOOLS: ClassVar[tuple[Any, ...]] = SEARCH_AND_PROFILE_TOOLS
    RESPONSE_FORMAT: ClassVar[Any | None] = PlannerAgentOutput

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
