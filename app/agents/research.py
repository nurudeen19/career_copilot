"""Research: skills, salary, demand — calls tools when wired."""

from app.tools import research_tools


def run(context: dict) -> dict:
    plan = context.get("plan") or {}
    return {
        "agent": "research",
        "required_skills": research_tools.fetch_required_skills_stub(plan),
        "salary_benchmarks": research_tools.fetch_salary_stub(plan),
        "market_demand": research_tools.fetch_market_demand_stub(plan),
        "sources": [],
        "notes": "Wire real search/API tools; merge results here.",
    }
