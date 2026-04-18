"""Career LangGraph: build_graph + run_graph, checkpointed memory; input checks live in ``app.guardrails``."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict

from app.agents.analyst import AnalystAgent
from app.agents.critic import CriticAgent
from app.agents.feedback import FeedbackAgent
from app.agents.planner import PlannerAgent
from app.agents.research import ResearchAgent
from app.agents.synthesizer import SynthesizerAgent
from app.core.agent_runtime import AgentRuntime, get_agent_runtime
from app.graph.checkpoint import dispose_checkpointer, get_checkpointer
from app.guardrails import run_user_input_guardrails
from app.schema.agent_outputs import (
    AnalystAgentOutput,
    CriticAgentOutput,
    FeedbackAgentOutput,
    PlannerAgentOutput,
    ResearchAgentOutput,
    SynthesizerAgentOutput,
)

_compiled: Any | None = None


class CareerGraphState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: NotRequired[str | None]
    user_feedback: NotRequired[str | None]
    validation_error: NotRequired[str | None]
    plan: NotRequired[dict[str, Any]]
    research: NotRequired[dict[str, Any]]
    analysis: NotRequired[dict[str, Any]]
    critique: NotRequired[dict[str, Any]]
    synthesis: NotRequired[dict[str, Any]]
    feedback: NotRequired[dict[str, Any]]


def reset_graph() -> None:
    global _compiled
    _compiled = None
    dispose_checkpointer()


def _user_id_prefix(state: CareerGraphState) -> list[AnyMessage]:
    uid = (state.get("user_id") or "").strip()
    if not uid:
        return []
    return [SystemMessage(content=f"User profile UUID for tools: {uid}")]


def _invoke_agent_graph(agent_graph: Any, messages: list[AnyMessage]) -> dict[str, Any]:
    return agent_graph.invoke({"messages": messages})


def _structured(result: dict[str, Any], model_cls: type[Any]) -> Any | None:
    sr = result.get("structured_response")
    return sr if isinstance(sr, model_cls) else None


def _validation_fail_node(state: CareerGraphState) -> dict[str, Any]:
    err = state.get("validation_error") or "Invalid input."
    return {"messages": [AIMessage(content=err)]}


def _route_after_input(state: CareerGraphState) -> Literal["validation_fail", "feedback", "planner"]:
    if state.get("validation_error"):
        return "validation_fail"
    if (state.get("user_feedback") or "").strip():
        return "feedback"
    return "planner"


def _route_after_planner(state: CareerGraphState) -> Literal["research", "user_handoff"]:
    plan = state.get("plan") or {}
    if plan.get("handoff") == "research":
        return "research"
    return "user_handoff"


def _user_handoff_node(state: CareerGraphState) -> dict[str, Any]:
    plan = state.get("plan") or {}
    text = (plan.get("assistant_message") or "").strip()
    return {"messages": [AIMessage(content=text)]}


def _make_input_validation_node(runtime: AgentRuntime):
    def node(state: CareerGraphState) -> dict[str, Any]:
        return run_user_input_guardrails(state, runtime.settings)

    return node


def _make_planner_node(runtime: AgentRuntime):
    def planner_node(state: CareerGraphState) -> dict[str, Any]:
        msgs = list(state.get("messages") or [])
        out = _invoke_agent_graph(PlannerAgent(runtime).graph, _user_id_prefix(state) + msgs)
        parsed = _structured(out, PlannerAgentOutput)
        if parsed is None:
            parsed = PlannerAgentOutput(
                handoff="user_clarify",
                notes="Structured planner output was missing; ask the user to restate their career goal.",
                assistant_message="",
            )
        return {"plan": parsed.model_dump()}

    return planner_node


def _make_research_node(runtime: AgentRuntime):
    def research_node(state: CareerGraphState) -> dict[str, Any]:
        msgs = list(state.get("messages") or [])
        ctx = [
            SystemMessage(
                content="Planner output (JSON):\n" + json.dumps(state.get("plan", {}), default=str, indent=2)
            )
        ]
        out = _invoke_agent_graph(ResearchAgent(runtime).graph, _user_id_prefix(state) + msgs + ctx)
        parsed = _structured(out, ResearchAgentOutput)
        return {"research": parsed.model_dump() if parsed else {}}

    return research_node


def _make_analyst_node(runtime: AgentRuntime):
    def analyst_node(state: CareerGraphState) -> dict[str, Any]:
        msgs = list(state.get("messages") or [])
        ctx = [
            SystemMessage(
                content="Planner:\n"
                + json.dumps(state.get("plan", {}), default=str)
                + "\nResearch:\n"
                + json.dumps(state.get("research", {}), default=str)
            )
        ]
        out = _invoke_agent_graph(AnalystAgent(runtime).graph, _user_id_prefix(state) + msgs + ctx)
        parsed = _structured(out, AnalystAgentOutput)
        return {"analysis": parsed.model_dump() if parsed else {}}

    return analyst_node


def _make_critic_node(runtime: AgentRuntime):
    def critic_node(state: CareerGraphState) -> dict[str, Any]:
        msgs = list(state.get("messages") or [])
        ctx = [
            SystemMessage(
                content="Planner:\n"
                + json.dumps(state.get("plan", {}), default=str)
                + "\nResearch:\n"
                + json.dumps(state.get("research", {}), default=str)
                + "\nAnalysis:\n"
                + json.dumps(state.get("analysis", {}), default=str)
            )
        ]
        out = _invoke_agent_graph(CriticAgent(runtime).graph, _user_id_prefix(state) + msgs + ctx)
        parsed = _structured(out, CriticAgentOutput)
        return {"critique": parsed.model_dump() if parsed else {}}

    return critic_node


def _make_synthesizer_node(runtime: AgentRuntime):
    def synthesizer_node(state: CareerGraphState) -> dict[str, Any]:
        msgs = list(state.get("messages") or [])
        ctx = [
            SystemMessage(
                content="Full pipeline JSON:\n"
                + json.dumps(
                    {
                        "plan": state.get("plan", {}),
                        "research": state.get("research", {}),
                        "analysis": state.get("analysis", {}),
                        "critique": state.get("critique", {}),
                    },
                    default=str,
                    indent=2,
                )[:24000]
            )
        ]
        out = _invoke_agent_graph(SynthesizerAgent(runtime).graph, _user_id_prefix(state) + msgs + ctx)
        parsed = _structured(out, SynthesizerAgentOutput)
        if parsed is None:
            return {"synthesis": {}, "messages": [AIMessage(content="I could not produce a final synthesis.")]}
        lines = [parsed.recommendation]
        for phase in parsed.roadmap:
            lines.append(f"\n## {phase.phase}\n" + "\n".join(f"- {a}" for a in phase.actions))
        if parsed.risks:
            lines.append("\n### Risks\n" + "\n".join(f"- {r}" for r in parsed.risks))
        body = "\n".join(lines).strip() or parsed.notes or "Here is your career summary."
        return {"synthesis": parsed.model_dump(), "messages": [AIMessage(content=body)]}

    return synthesizer_node


def _make_feedback_node(runtime: AgentRuntime):
    def feedback_node(state: CareerGraphState) -> dict[str, Any]:
        msgs = list(state.get("messages") or [])
        fb_raw = (state.get("user_feedback") or "").strip()
        ctx = [SystemMessage(content=f"User dissatisfaction or correction:\n{fb_raw}")]
        out = _invoke_agent_graph(FeedbackAgent(runtime).graph, _user_id_prefix(state) + msgs + ctx)
        parsed = _structured(out, FeedbackAgentOutput)
        hints = parsed.adaptation_hints if isinstance(parsed, FeedbackAgentOutput) else []
        notes = parsed.notes if isinstance(parsed, FeedbackAgentOutput) else ""
        re_plan = SystemMessage(
            content=(
                "Return to planning. Prior plan JSON (may revise, do not blindly repeat):\n"
                + json.dumps(state.get("plan", {}), default=str)[:8000]
                + "\nIncorporate the feedback above; set handoff to research only when ready."
                f"\nAdaptation hints: {json.dumps(hints)}\nFeedback notes: {notes}"
            )
        )
        return {
            "feedback": parsed.model_dump() if parsed else {},
            "user_feedback": "",
            "messages": [re_plan],
        }

    return feedback_node


def _compile_graph(runtime: AgentRuntime, checkpointer: Any) -> Any:
    g = StateGraph(CareerGraphState)
    g.add_node("input_validation", _make_input_validation_node(runtime))
    g.add_node("validation_fail", _validation_fail_node)
    g.add_node("planner", _make_planner_node(runtime))
    g.add_node("research", _make_research_node(runtime))
    g.add_node("analyst", _make_analyst_node(runtime))
    g.add_node("critic", _make_critic_node(runtime))
    g.add_node("synthesizer", _make_synthesizer_node(runtime))
    g.add_node("feedback", _make_feedback_node(runtime))
    g.add_node("user_handoff", _user_handoff_node)

    g.add_edge(START, "input_validation")
    g.add_conditional_edges(
        "input_validation",
        _route_after_input,
        {"validation_fail": "validation_fail", "feedback": "feedback", "planner": "planner"},
    )
    g.add_edge("validation_fail", END)
    g.add_conditional_edges(
        "planner",
        _route_after_planner,
        {"research": "research", "user_handoff": "user_handoff"},
    )
    g.add_edge("user_handoff", END)
    g.add_edge("research", "analyst")
    g.add_edge("analyst", "critic")
    g.add_edge("critic", "synthesizer")
    g.add_edge("synthesizer", END)
    g.add_edge("feedback", "planner")

    return g.compile(checkpointer=checkpointer)


def build_graph(runtime: AgentRuntime | None = None) -> Any:
    """Compile the career workflow once per process (with Postgres or SQLite checkpointing)."""
    global _compiled
    if _compiled is not None:
        return _compiled
    r = runtime or get_agent_runtime()
    cp = get_checkpointer(r.settings)
    _compiled = _compile_graph(r, cp)
    return _compiled


def run_graph(
    user_message: str,
    *,
    thread_id: str,
    user_id: str | None = None,
    user_feedback: str | None = None,
    runtime: AgentRuntime | None = None,
) -> dict[str, Any]:
    """Execute one graph turn. Re-use ``thread_id`` to continue checkpointed memory."""
    graph = build_graph(runtime or get_agent_runtime())
    initial: dict[str, Any] = {"messages": [HumanMessage(content=user_message)]}
    if user_id:
        initial["user_id"] = user_id
    if user_feedback:
        initial["user_feedback"] = user_feedback
    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    final_state = graph.invoke(initial, config=cfg)
    return {
        "thread_id": thread_id,
        "user_message": user_message,
        "messages": final_state.get("messages"),
        "plan": final_state.get("plan"),
        "research": final_state.get("research"),
        "analysis": final_state.get("analysis"),
        "critique": final_state.get("critique"),
        "synthesis": final_state.get("synthesis"),
        "feedback": final_state.get("feedback"),
    }


def run_graph_continue(
    *,
    thread_id: str,
    user_message: str,
    user_id: str | None = None,
    runtime: AgentRuntime | None = None,
) -> dict[str, Any]:
    """Append a user turn to an existing ``thread_id`` (loads prior checkpoint)."""
    graph = build_graph(runtime or get_agent_runtime())
    update = {"messages": [HumanMessage(content=user_message)]}
    if user_id:
        update["user_id"] = user_id
    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    final_state = graph.invoke(update, config=cfg)
    return {
        "thread_id": thread_id,
        "user_message": user_message,
        "messages": final_state.get("messages"),
        "plan": final_state.get("plan"),
        "research": final_state.get("research"),
        "analysis": final_state.get("analysis"),
        "critique": final_state.get("critique"),
        "synthesis": final_state.get("synthesis"),
        "feedback": final_state.get("feedback"),
    }
