"""Research: skills, salary, demand — calls tools when wired."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import ResearchAgentOutput
from app.tools import SEARCH_AND_PROFILE_TOOLS, research_tools


class ResearchAgent:
    role: ClassVar[AgentName] = "research"
    INSTRUCTIONS: ClassVar[str] = (
        "You are the labor-market researcher (runs only after the planner set handoff=research). "
        "Use tavily_web_search and brave_web_search for evidence on skills, salary bands, and hiring signals. "
        "When the user is authenticated in session, call get_my_saved_profile (no arguments) to align with saved profile fields. "
        "Prefer short queries. Cite tool JSON (titles/URLs) in sources. "
        "Your final reply MUST match the structured output schema."
    )
    TOOLS: ClassVar[tuple[Any, ...]] = SEARCH_AND_PROFILE_TOOLS
    RESPONSE_FORMAT: ClassVar[Any | None] = ResearchAgentOutput

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
