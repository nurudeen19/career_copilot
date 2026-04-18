"""Bundle of pipeline agents for a single ``AgentRuntime``."""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.analyst import AnalystAgent
from app.agents.critic import CriticAgent
from app.agents.feedback import FeedbackAgent
from app.agents.planner import PlannerAgent
from app.agents.research import ResearchAgent
from app.agents.synthesizer import SynthesizerAgent
from app.core.agent_runtime import AgentRuntime, get_agent_runtime


@dataclass(frozen=True)
class AgentBundle:
    runtime: AgentRuntime
    planner: PlannerAgent
    research: ResearchAgent
    analyst: AnalystAgent
    critic: CriticAgent
    synthesizer: SynthesizerAgent
    feedback: FeedbackAgent


def get_agent_bundle(runtime: AgentRuntime | None = None) -> AgentBundle:
    r = runtime if runtime is not None else get_agent_runtime()
    return AgentBundle(
        runtime=r,
        planner=PlannerAgent(r),
        research=ResearchAgent(r),
        analyst=AnalystAgent(r),
        critic=CriticAgent(r),
        synthesizer=SynthesizerAgent(r),
        feedback=FeedbackAgent(r),
    )


def reset_agent_bundle() -> None:
    """Reserved for future bundle-level caches (currently a no-op)."""
    return None
