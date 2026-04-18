"""LangChain web search tools: Tavily via langchain-tavily, Brave via REST (rich results)."""

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


def _brave_row_to_hit(rank: int, row: dict[str, Any]) -> SearchHit:
    description = str(row.get("description") or "")
    snippets_raw = row.get("extra_snippets")
    parts: list[str] = []
    if description:
        parts.append(description)
    if isinstance(snippets_raw, list):
        for s in snippets_raw:
            if isinstance(s, str) and s.strip():
                parts.append(s.strip())
    summary = _truncate("\n\n".join(parts)) if parts else ""

    meta: dict[str, Any] = {}
    for key in ("page_age", "age", "language", "family_friendly", "type"):
        if row.get(key) is not None:
            meta[key] = row.get(key)

    # Some Brave payloads include a short subtype or source hint
    if row.get("meta_url") and isinstance(row["meta_url"], dict):
        meta["site"] = row["meta_url"].get("hostname")

    score = row.get("confidence") or row.get("score")
    rel = float(score) if isinstance(score, (int, float)) else None

    return SearchHit(
        rank=rank,
        title=str(row.get("title", "")),
        url=str(row.get("url", "")),
        summary=summary,
        source="brave",
        relevance_score=rel,
        meta=meta,
    )


def _brave_data_to_response(query: str, data: dict[str, Any]) -> SearchToolResponse:
    overview: str | None = None
    summarizer = data.get("summarizer")
    if isinstance(summarizer, dict):
        # Shape varies by plan; keep best-effort string for agents
        overview = summarizer.get("summary") or summarizer.get("text")
        if overview is not None and not isinstance(overview, str):
            overview = str(overview)

    web = data.get("web")
    raw = web.get("results") if isinstance(web, dict) else None
    if not isinstance(raw, list):
        return SearchToolResponse(
            provider="brave",
            query=query,
            overview=overview,
            error="Missing or invalid 'web.results' in Brave response.",
        )

    hits = [_brave_row_to_hit(i, row) for i, row in enumerate(raw, start=1) if isinstance(row, dict)]
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
    """Search the web with Brave (REST). Richer snippets + extra_snippets. Returns JSON: SearchToolResponse schema."""
    key = get_settings().brave_search_api_key
    q = (query or "").strip()
    if not key:
        return _empty_response("brave", q, "Brave Search is not configured: set BRAVE_SEARCH_API_KEY.")
    if not q:
        return _empty_response("brave", q, "Query is empty.")

    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={
                    "q": q,
                    "count": 10,
                    "text_decorations": False,
                    "extra_snippets": True,
                },
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": key,
                },
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as exc:
        return SearchToolResponse(provider="brave", query=q, error=f"Brave request failed: {exc}").to_agent_text()

    if not isinstance(data, dict):
        return SearchToolResponse(provider="brave", query=q, error="Unexpected Brave response type.").to_agent_text()

    return _brave_data_to_response(q, data).to_agent_text()


SEARCH_TOOLS = (tavily_web_search, brave_web_search)
