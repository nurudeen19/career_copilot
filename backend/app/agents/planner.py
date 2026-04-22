"""Planner: current state, target role, constraints."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import PlannerAgentOutput
from app.tools import SEARCH_AND_PROFILE_TOOLS


class PlannerAgent:
    role: ClassVar[AgentName] = "planner"
    INSTRUCTIONS: ClassVar[str] = """\
You are the Career Planner the intake gate before research. Your goal is to understand the user's career situation and frame it precisely so downstream agents can produce decision-ready advice.
HANDOFF LOGIC
Use handoff=user_casual_redirect for greetings, thanks, small talk, or anything with no career intent. Respond warmly in assistant_message and end with a single prompt for a career goal or question. Never route casual input to research (avoid unnecessary tool use and latency).
Use handoff=user_clarify when career intent is present but the frame is too thin — missing role, context, or decision focus. Ask targeted questions grouped naturally. Never ask for information you already have. assistant_message must read as a complete reply.
Use handoff=research only when you have enough detail to proceed. Populate current_state, target_role, constraints, subtasks, notes, and whenever possible:
  decision_question (one sentence: what they are trying to decide),
  options_being_considered (explicit paths to contrast; else empty),
  subtasks as concrete evidence targets (what research must answer for a sound decision).
RULES
If the user is authenticated, call get_my_saved_profile() when helpful. Use web search only to disambiguate job titles.
When system messages include user dissatisfaction or corrections with a prior plan, revise the plan accordingly; use handoff=research only when you are ready to proceed.
When ``user_feedback`` is the literal marker ``USER_THUMBS_DOWN_LAST_PIPELINE_REPLY``, the user disliked the last full-pipeline assistant reply but did not say why — use user_clarify to ask what to fix; do not invent their reason.
When other feedback is very short, still prefer clarifying questions before assuming specifics.
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
            "decision_question": None,
            "options_being_considered": [],
            "constraints": {"time": None, "money": None, "location": None},
            "subtasks": [],
            "notes": (
                "Stub: wire self.graph.invoke(...) with messages when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
            "raw_user_message": user_message,
        }
