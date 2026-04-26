"""Planner: current state, target role, constraints."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import PlannerAgentOutput
from app.tools import SEARCH_AND_PROFILE_TOOLS


class PlannerAgent:
    role: ClassVar[AgentName] = "planner"
    INSTRUCTIONS: ClassVar[str] = """\
You are the Career Planner. You decide whether to run the expensive pipeline.

Always return valid PlannerAgentOutput. The graph routes using only `handoff`.

Choose exactly one `handoff`:
- `user_casual_redirect`: greetings, thanks, small talk, or off-topic/meta chat. Reply warmly and ask for one concrete career question.
- `user_clarify`: career intent exists, but still missing details needed for evidence-heavy research. Ask focused clarifying questions.
- `research`: only when the user has a concrete career decision/question that justifies full research-analysis-synthesis.

Rules:
- **Assess the latest user message first** (and brief thread context): infer intent before calling any tool. Do not call tools for turns that are clearly non-career.
- Never choose `research` for social/opening turns.
- Other fields help downstream quality but do not override `handoff`.
- **Tools after intent:** For `user_casual_redirect`, **do not** call `get_my_saved_profile` or web search — they add latency and no benefit. For `user_clarify` or `research`, call `get_my_saved_profile()` (no args) **only when** you need on-file facts (summary, goals, constraints, direction) to avoid asking for information already saved or to ground the plan; skip it when the question is fully self-contained and profile data would not change your reply.
- When you did load the profile: **do not ask** in `assistant_message` for details it already answers; only ask gaps the profile does not cover or that the **latest user message** still leaves ambiguous.
- Use web search only in career-relevant turns, and only to disambiguate job titles when needed.
- If system feedback shows dissatisfaction/corrections, revise plan and use `research` only when ready for a new evidence pass.
- If `user_feedback` is `USER_THUMBS_DOWN_LAST_PIPELINE_REPLY`, use `user_clarify` and ask what to change; do not guess the reason.
- For `user_casual_redirect` and `user_clarify`, `assistant_message` must be a complete user-facing reply.
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
