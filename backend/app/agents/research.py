"""Research: skills, salary, demand — calls tools when wired."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.tools import research_tools


class ResearchAgent:
    role: ClassVar[AgentName] = "research"
    INSTRUCTIONS: ClassVar[str] = (
        "You are a labor-market and skills researcher. Use available tools to gather "
        "required skills, salary benchmarks, and demand signals for the user's target path. "
        "Cite or summarize sources when tools return them."
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
        return {
            "agent": "research",
            "required_skills": research_tools.fetch_required_skills_stub(plan),
            "salary_benchmarks": research_tools.fetch_salary_stub(plan),
            "market_demand": research_tools.fetch_market_demand_stub(plan),
            "sources": [],
            "notes": (
                "Stub: register LangChain tools on TOOLS, then invoke self.graph. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
        }
