"""Research: skills, salary, demand — calls tools when wired."""

from typing import Any, ClassVar

from app.config.agents import AgentName
from app.core.agent_runtime import AgentRuntime
from app.schema.agent_outputs import ResearchAgentOutput
from app.tools import SEARCH_AND_PROFILE_TOOLS, research_tools


class ResearchAgent:
    role: ClassVar[AgentName] = "research"
    INSTRUCTIONS: ClassVar[str] = ("""\
        You are the labor-market researcher. Run only when planner chose `handoff=research`.
        Gather evidence with `tavily_web_search` and `brave_web_search` using short queries.

        Put the full findings in `research_report` (required).
        - Fill `comparison_summary` when comparing paths/switches.
        - Fill `evidence_based_next_steps` with evidence-backed actions.
        - Mirror critical facts in `key_facts`; list unknowns in `open_questions`.
        - Add citations in `sources` (title/url when available).
        - Only fill `salary_benchmarks` and `market_demand` when evidence supports them.

        `get_my_saved_profile()` (no args): this user's saved career summary, goals, and direction from the DB. Call it **before** heavy search when it can anchor role, geography, or stated preferences — align findings with it; do not contradict saved goals without evidence the user changed their mind.
        Return valid structured output.
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
