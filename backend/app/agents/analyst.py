"""Analyst: skill gap, feasibility, timeline."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime


class AnalystAgent:
    role: ClassVar[AgentName] = "analyst"
    INSTRUCTIONS: ClassVar[str] = (
        "You are a career feasibility analyst. From the plan and research artifacts, "
        "identify skill gaps, estimate feasibility, and propose a realistic timeline. "
        "Be direct about tradeoffs and missing information."
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
        plan = context.get("plan") or {}
        research = context.get("research") or {}
        return {
            "agent": "analyst",
            "skill_gaps": [],
            "feasibility_score": None,
            "timeline_estimate": None,
            "notes": (
                "Stub: invoke self.graph with plan + research context when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
            "inputs_summary": {"plan_keys": list(plan.keys()), "research_keys": list(research.keys())},
        }
