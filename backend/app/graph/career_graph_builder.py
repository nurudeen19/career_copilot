"""Graph construction and compile-time caching for the career workflow."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.core.agent_runtime import AgentRuntime, get_agent_runtime
from app.graph.career_graph_nodes import (
    CareerGraphState,
    make_analyst_node,
    make_critic_node,
    make_input_validation_node,
    make_planner_node,
    make_research_node,
    make_synthesizer_node,
    route_after_input,
    route_after_planner,
    user_handoff_node,
    validation_fail_node,
)
from app.graph.checkpoint import dispose_checkpointer, get_checkpointer

_compiled: Any | None = None


def reset_graph() -> None:
    global _compiled
    _compiled = None
    dispose_checkpointer()


def _compile_graph(runtime: AgentRuntime, checkpointer: Any) -> Any:
    g = StateGraph(CareerGraphState)
    g.add_node("input_validation", make_input_validation_node(runtime))
    g.add_node("validation_fail", validation_fail_node)
    g.add_node("planner", make_planner_node(runtime))
    g.add_node("research", make_research_node(runtime))
    g.add_node("analyst", make_analyst_node(runtime))
    g.add_node("critic", make_critic_node(runtime))
    g.add_node("synthesizer", make_synthesizer_node(runtime))
    g.add_node("user_handoff", user_handoff_node)

    g.add_edge(START, "input_validation")
    g.add_conditional_edges(
        "input_validation",
        route_after_input,
        {"validation_fail": "validation_fail", "planner": "planner"},
    )
    g.add_edge("validation_fail", END)
    g.add_conditional_edges(
        "planner",
        route_after_planner,
        {"research": "research", "user_handoff": "user_handoff"},
    )
    g.add_edge("user_handoff", END)
    g.add_edge("research", "analyst")
    g.add_edge("analyst", "critic")
    g.add_edge("critic", "synthesizer")
    g.add_edge("synthesizer", END)

    return g.compile(checkpointer=checkpointer)


def compile_career_graph_for_visualization(runtime: AgentRuntime | None = None) -> Any:
    """Compile the workflow with an in-memory checkpointer for structure export (PNG, docs)."""
    from langgraph.checkpoint.memory import MemorySaver

    r = runtime or get_agent_runtime()
    return _compile_graph(r, MemorySaver())


def build_graph(runtime: AgentRuntime | None = None) -> Any:
    """Compile the career workflow once per process (with Postgres or SQLite checkpointing)."""
    global _compiled
    if _compiled is not None:
        return _compiled
    r = runtime or get_agent_runtime()
    cp = get_checkpointer(r.settings)
    _compiled = _compile_graph(r, cp)
    return _compiled

