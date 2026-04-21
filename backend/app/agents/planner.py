"""Planner: current state, target role, constraints."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import PlannerAgentOutput
from app.tools import SEARCH_AND_PROFILE_TOOLS


class PlannerAgent:
    role: ClassVar[AgentName] = "planner"
    INSTRUCTIONS: ClassVar[str] = """\
You are the career planner (gate before research).
Handle greetings, thanks, small talk, jokes, or off-topic chat with handoff=user_casual_redirect. Respond naturally in assistant_message and prompt for a clear career goal or question (one short sentence).
Do not send casual or meta input to research (avoid unnecessary tool use and latency).
If the user's intent is vague, use handoff=user_clarify with a concise assistant_message asking targeted questions.
Use handoff=research only when you have enough detail to proceed (populate current_state, target_role, constraints, subtasks, notes).
If the user is authenticated, call get_my_saved_profile (no args) when helpful. Use web search only to disambiguate job titles.
assistant_message is required for user_clarify and user_casual_redirect, and must read like a complete assistant reply.
"""
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
