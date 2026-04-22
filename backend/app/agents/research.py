"""Research: skills, salary, demand — calls tools when wired."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import ResearchAgentOutput
from app.tools import SEARCH_AND_PROFILE_TOOLS, research_tools


class ResearchAgent:
    role: ClassVar[AgentName] = "research"
    INSTRUCTIONS: ClassVar[str] = ("""\
        You are the labor-market researcher. You run only after the planner sets handoff=research.
        Use tavily_web_search and brave_web_search to gather evidence. Prefer short search queries. Not every plan requires salary or hiring-demand data — only populate salary_benchmarks and market_demand when your searches genuinely support those dimensions; otherwise leave them empty.

        research_report is mandatory: write the full findings narrative there so downstream agents do not depend on sparse fields. Fill comparison_summary when the plan compares paths or a switch. Fill evidence_based_next_steps with actions grounded in your findings, not generic advice. Mirror critical facts in key_facts and list unresolved gaps in open_questions. Populate sources from tool results (titles and URLs).

        If the user is authenticated, call get_my_saved_profile() when it would improve the relevance of your findings.
        Your final reply must match the structured output schema.
    """)
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
            "research_report": (
                "Stub research report: wire self.graph.invoke with planner context when ready. "
                f"Configured: {agent_llm_config.model_provider}:{agent_llm_config.model}."
            ),
            "required_skills": research_tools.fetch_required_skills_stub(plan),
            "salary_benchmarks": research_tools.fetch_salary_stub(plan),
            "market_demand": research_tools.fetch_market_demand_stub(plan),
            "sources": [],
            "comparison_summary": "",
            "evidence_based_next_steps": [],
            "research_method_notes": "Stub path — no live tools invoked.",
        }
