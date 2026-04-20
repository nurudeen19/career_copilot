"""LangChain web search tools: Tavily via langchain-tavily, Brave via REST (LLM Context API for agent-grade excerpts)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

import httpx
from langchain_core.tools import ToolException, tool
from langchain_tavily import TavilySearch

from app.config.settings import get_settings
from app.schema.search import SearchHit, SearchToolResponse

_MAX_SUMMARY_CHARS = 12_000


def _truncate(text: str, max_len: int = _MAX_SUMMARY_CHARS) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 24].rstrip() + "\n…(truncated)"


def _empty_response(provider: Literal["tavily", "brave"], query: str, error: str) -> str:
    return SearchToolResponse(provider=provider, query=query, error=error).to_agent_text()


@lru_cache(maxsize=8)
def _tavily_search_client(api_key: str) -> TavilySearch:
    """One TavilySearch instance per API key (langchain-tavily / official integration)."""
    return TavilySearch(
        tavily_api_key=api_key,
        max_results=8,
        search_depth="basic",
        include_answer="basic",
        include_raw_content="markdown",
    )


def _tavily_raw_to_response(query: str, raw: dict[str, Any]) -> SearchToolResponse:
    if not isinstance(raw, dict):
        return SearchToolResponse(provider="tavily", query=query, error="Unexpected Tavily response type.")

    err = raw.get("error")
    if err is not None:
        return SearchToolResponse(provider="tavily", query=query, error=str(err))

    overview = raw.get("answer")
    if overview is not None and not isinstance(overview, str):
        overview = str(overview)

    rows = raw.get("results")
    if not isinstance(rows, list):
        return SearchToolResponse(
            provider="tavily",
            query=query,
            overview=overview,
            error="Missing or invalid 'results' in Tavily response.",
        )

    hits: list[SearchHit] = []
    for i, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        title = str(row.get("title", ""))
        url = str(row.get("url", ""))
        content = str(row.get("content", ""))
        raw_content = str(row.get("raw_content") or "")
        if raw_content:
            body = f"{content}\n\n### Page content (markdown)\n{raw_content}"
        else:
            body = content
        score = row.get("score")
        rel = float(score) if isinstance(score, (int, float)) else None
        meta: dict[str, Any] = {}
        if row.get("favicon"):
            meta["favicon"] = row.get("favicon")
        hits.append(
            SearchHit(
                rank=i,
                title=title,
                url=url,
                summary=_truncate(body),
                source="tavily",
                relevance_score=rel,
                meta=meta,
            )
        )

    return SearchToolResponse(provider="tavily", query=query, overview=overview, hits=hits)


def _brave_snippets_to_summary(snippets: Any) -> str:
    """Join LLM Context snippet list (strings or serialized structures) into one summary block."""
    if not isinstance(snippets, list):
        return ""
    parts: list[str] = []
    for s in snippets:
        if isinstance(s, str) and s.strip():
            parts.append(s.strip())
        elif s is not None:
            t = str(s).strip()
            if t:
                parts.append(t)
    return _truncate("\n\n".join(parts)) if parts else ""


def _brave_llm_context_to_response(query: str, data: dict[str, Any]) -> SearchToolResponse:
    """
    Map Brave ``/res/v1/llm/context`` JSON into ``SearchToolResponse``.

    See: https://api-dashboard.search.brave.com/documentation/services/llm-context
    """
    grounding = data.get("grounding")
    if not isinstance(grounding, dict):
        return SearchToolResponse(
            provider="brave",
            query=query,
            error="Missing or invalid 'grounding' in Brave LLM Context response.",
        )

    sources_raw = data.get("sources")
    sources_meta: dict[str, Any] = sources_raw if isinstance(sources_raw, dict) else {}

    hits: list[SearchHit] = []
    rank = 0

    def _append_block(block: dict[str, Any], *, kind: str) -> None:
        nonlocal rank
        url = str(block.get("url") or "").strip()
        title = str(block.get("title") or "").strip()
        summary = _brave_snippets_to_summary(block.get("snippets"))
        if not url and not summary:
            return
        rank += 1
        meta: dict[str, Any] = {"brave_grounding": kind}
        src = sources_meta.get(url) if url else None
        if isinstance(src, dict):
            if src.get("hostname"):
                meta["site"] = src.get("hostname")
            if src.get("age") is not None:
                meta["age"] = src.get("age")
            if src.get("title") and not title:
                title = str(src["title"])

        hits.append(
            SearchHit(
                rank=rank,
                title=title or url or f"Source {rank}",
                url=url,
                summary=summary or "(no extracted snippets)",
                source="brave",
                relevance_score=None,
                meta=meta,
            )
        )

    for row in grounding.get("generic") or []:
        if isinstance(row, dict):
            _append_block(row, kind="generic")

    poi = grounding.get("poi")
    if isinstance(poi, dict):
        _append_block(poi, kind="poi")

    for row in grounding.get("map") or []:
        if isinstance(row, dict):
            _append_block(row, kind="map")

    if not hits:
        return SearchToolResponse(
            provider="brave",
            query=query,
            overview="Brave LLM Context returned no grounded excerpts for this query.",
            hits=[],
        )

    overview_chunks: list[str] = []
    for h in hits[:3]:
        if h.summary and h.summary != "(no extracted snippets)":
            overview_chunks.append(h.summary[:500])
        if sum(len(x) for x in overview_chunks) > 1400:
            break
    overview = _truncate("\n---\n".join(overview_chunks), max_len=2000) if overview_chunks else None

    return SearchToolResponse(provider="brave", query=query, overview=overview, hits=hits)


@tool
def tavily_web_search(query: str) -> str:
    """Search the web with Tavily (LangChain integration). Returns JSON: SearchToolResponse schema."""
    key = get_settings().tavily_api_key
    q = (query or "").strip()
    if not key:
        return _empty_response("tavily", q, "Tavily is not configured: set TAVILY_API_KEY in the environment.")
    if not q:
        return _empty_response("tavily", q, "Query is empty.")

    client = _tavily_search_client(key)
    try:
        raw = client.invoke({"query": q})
    except ToolException as exc:
        return SearchToolResponse(provider="tavily", query=q, error=str(exc)).to_agent_text()
    except Exception as exc:  # noqa: BLE001 — surface to agent as structured error
        return SearchToolResponse(provider="tavily", query=q, error=str(exc)).to_agent_text()

    if not isinstance(raw, dict):
        return SearchToolResponse(provider="tavily", query=q, error="Unexpected Tavily return type.").to_agent_text()

    return _tavily_raw_to_response(q, raw).to_agent_text()


@tool
def brave_web_search(query: str) -> str:
    """
    Search the web with Brave **LLM Context** (REST): pre-extracted, relevance-filtered passages per URL,
    optimized for agents / RAG (vs. classic web search links + short snippets only).

    Returns JSON: SearchToolResponse schema.
    """
    key = get_settings().brave_search_api_key
    q = (query or "").strip()
    if not key:
        return _empty_response("brave", q, "Brave Search is not configured: set BRAVE_SEARCH_API_KEY.")
    if not q:
        return _empty_response("brave", q, "Query is empty.")

    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.get(
                "https://api.search.brave.com/res/v1/llm/context",
                params={
                    "q": q,
                    "count": 15,
                    "maximum_number_of_urls": 15,
                    "maximum_number_of_tokens": 8192,
                    "context_threshold_mode": "balanced",
                },
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": key,
                },
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as exc:
        return SearchToolResponse(provider="brave", query=q, error=f"Brave LLM Context request failed: {exc}").to_agent_text()

    if not isinstance(data, dict):
        return SearchToolResponse(provider="brave", query=q, error="Unexpected Brave response type.").to_agent_text()

    return _brave_llm_context_to_response(q, data).to_agent_text()


SEARCH_TOOLS = (tavily_web_search, brave_web_search)
