# Design Decisions

This document records key architectural decisions and their rationales. Each section follows an ADR (Architecture Decision Record) format.

---

## ADR-001: Modular Settings Configuration

### Context

Career Copilot integrates with multiple external services (LLMs, search, databases, tracing). Configuration needs to support:
- Using a single file becomes hard to navigate
- Per-agent customization requirements
- The possibilities of increased env vars

### Decision

Implement **modular settings hierarchy** using Pydantic Settings in `backend/app/config/`:

```
settings.py          # Base app settings (database, CORS, debug)
app_settings.py      # Feature flags, timeouts
agents.py            # Per-agent LLM configurations
rate_limits.py       # Rate limiting policies
workflow.py          # Workflow stage configs
prompt_guard_config.py # Safety thresholds
```

**Configuration sources (in order):**
1. Environment variables (`.env`)
2. Config files (YAML/JSON, optional)
3. Hardcoded defaults

### Rationale

- **Separation of concerns:** Each service has its own config class
- **Type safety:** Pydantic validates at startup (fail fast)
- **Environment isolation:** Easy to override per-environment
- **Feature toggles:** Optional components don't break if not configured
- **Testing:** Stub configs for fast unit tests

### Trade-offs

- **Complexity:** More files, but clearer intent
- **Verbosity:** More boilerplate vs. flat config dict
- **Performance:** Settings validated once at startup (negligible)

---

## ADR-002: Multiple LLM Providers

### Context

A single LLM provider creates vendor lock-in and service dependency risks:
- Provider outages cause cascading failures
- Pricing varies; switching requires code changes
- Some models excel at specific tasks (reasoning, speed, cost)

### Decision

Support **multiple LLM providers with fallback chains**:

**Supported providers:**
- **OpenAI** (GPT-4o-mini as default)
- **Groq** (Fast inference, lower cost)
- **Google GenAI** (Gemini 2.5 flash, etc)
- **OpenRouter** (Meta gateway for switching)

```python
# Per-agent configuration example
agent_config = {
    "planner": {
        "primary": "groq",      # Fast + cheap
        "fallback": ["openai"]  # Fallback to quality
    },
    "synthesizer": {
        "primary": "openai",    # High quality
        "fallback": ["groq"]    # Cost fallback
    }
}
```

### Rationale

- **Resilience:** If primary provider is down, fallback automatically
- **Cost optimization:** Use cheaper models as primary, expensive as fallback
- **Task-specific:** Assign best-fit provider per agent
- **Future-proof:** Easy to add new providers

### Trade-offs

- **API key management:** 4+ secrets to configure
- **Testing complexity:** Mock multiple providers
- **Token consistency:** Different models → different response styles

---

## ADR-003: LangGraph for Workflow Orchestration

### Context

Career Copilot requires:
- Multi-stage agent pipeline (planner → researcher → analyst → critic → synthesizer)
- State persistence across stages
- Feedback loops (user can re-enter at planner with "thumbs down")
- Resumable workflows (user disconnects, reconnects later)

### Decision

Use **LangGraph** for workflow definition and management:

```python
graph = StateGraph(WorkflowState)
graph.add_node("planner", planner_agent)
graph.add_node("researcher", researcher_agent)
graph.add_node("analyst", analyst_agent)
graph.add_node("critic", critic_agent)
graph.add_node("synthesizer", synthesizer_agent)

# Checkpointing for persistence
compiled = graph.compile(checkpointer=PostgresCheckpointer())
```

### Rationale

- **State management:** SharedState object flows through pipeline
- **Checkpointing:** Built-in support for resuming workflows
- **Visualization:** Auto-generates workflow diagrams (PNG, Mermaid)
- **LLM-native:** LangChain integration seamless
- **Testability:** Graph structure is data, easy to unit test

### Trade-offs

- **Vendor lock-in:** LangGraph is LangChain's proprietary tool
- **Learning curve:** Graph concepts unfamiliar to some developers
- **Debugging:** Complex state transitions can be hard to trace

---

## ADR-004: FastAPI + SSE for Real-Time Streaming

### Context

Users expect **real-time feedback** as agents progress through stages. Options:
1. Polling: Client requests `/status` every N seconds
2. WebSocket: Full-duplex connection
3. SSE: Server-Sent Events (one-way server→client)
4. Long-polling: HTTP with persistent connection

### Decision

Use **Server-Sent Events (SSE)** for streaming workflow progress:

```python
@app.get("/workflow/{workflow_id}/stream")
async def stream_workflow(workflow_id: str):
    async def event_generator():
        for event in workflow.stream():
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Rationale

- **Simplicity:** Easier than WebSocket for one-way data (server→client)
- **Native browser support:** Works with EventSource API
- **HTTP/2 compatible:** Better than long-polling
- **Automatic reconnect:** Browser handles disconnections
- **Stateless:** No server-side connection state needed

### Trade-offs

- **One-way only:** Can't send real-time messages to server (use REST for that)
- **Connection limit:** Browsers limit SSE per domain
- **Fallback:** IE11 not supported (acceptable for modern apps)

---


## ADR-005: Pydantic for Schema Validation

### Context

API endpoints need to validate incoming JSON (request bodies, query params). Options:
1. Manual validation
2. JSON Schema validators
3. Pydantic models
4. Custom decorators

### Decision

Use **Pydantic v2 models** for all request/response schemas:

```python
class WorkflowStartRequest(BaseModel):
    question: str
    user_id: str

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    stages: list[str]

@app.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(req: WorkflowStartRequest) -> WorkflowResponse:
    # FastAPI auto-validates req against schema
    ...
```

### Rationale

- **Auto-documentation:** OpenAPI/Swagger generated from models
- **Type safety:** IDE autocomplete, mypy support
- **Serialization:** Built-in JSON encoding/decoding
- **Validation:** Declarative, composable validators
- **Coercion:** Automatic type conversion (str → int)

### Trade-offs

- **Overhead:** Small runtime cost for validation (negligible)
- **Complexity:** Learning Pydantic validators
- **Schema evolution:** Breaking changes need careful migration

---

## ADR-006: uv Package Manager

### Context

Python packaging tools vary: pip, Poetry, Conda, pdm. Options:
1. pip + requirements.txt (simple, limited)
2. Poetry (popular, slower)
3. Conda (powerful but heavy)
4. uv (fast, modern, emerging)

### Decision

Use **uv for dependency management** with native CPU/GPU extras support ~1GB CPU, ~4GB GPU:

```toml
[project.optional-dependencies]
transformer-cpu = ["transformers>=4.51", "torch>=2.6", "accelerate>=1.0"]
transformer-gpu = ["transformers>=4.51", "torch>=2.6", "accelerate>=1.0"]

[tool.uv]
conflicts = [[{extra = "cpu"}, {extra = "gpu"}]]
sources.torch = [{index = "pytorch-cpu", extra = "cpu"}, ...]
```

### Rationale

- **Speed:** 10-100x faster than pip/Poetry
- **Lock file:** `uv.lock` ensures reproducible builds
- **Native extras:** Clean way to handle CPU/GPU variants
- **Docker integration:** Reduces image size vs. pip
- **Modern:** Actively maintained, used by HuggingFace

### Trade-offs

- **Newness:** Emerging tool, not battle-tested as pip
- **Ecosystem:** Smaller community than pip/Poetry

---


## ADR-007: PostgreSQL + Alembic for Schema Migrations

### Context

Database schema evolves over time. Options:
1. Manual SQL scripts (error-prone)
2. SQLAlchemy declarative + auto-migrations (risky in production)
3. Alembic (industry standard, safe)

### Decision

Use **Alembic for schema migrations**:

```bash
# Generate migration
alembic revision --autogenerate -m "Add workflow_id to conversations"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Rationale

- **Safety:** Review migrations before applying
- **Reversibility:** Downgrade support
- **Tracking:** Git history of schema changes
- **Production-ready:** Handles data migrations
- **Standard:** Industry best practice

---

## ADR-008: Guardrails (Llama Prompt Guard)

### Context

Malicious prompts (jailbreaks, injections) should be detected. Options:
1. No guardrails (trust user input, risky)
2. Rule-based filters (simple but not robust)
3. ML guardrails model (effective but requires resources)

### Decision

Make **Llama Prompt Guard** via extras:

```bash
# Install with guardrails
uv sync --extra transformer-cpu

# Or gpu version significantly larger
uv sync --extra transformer-gpu
```

### Rationale

- **Flexibility:** Smaller deployments can skip GPU-intensive models
- **Cost:** Guardrails adds ~1.12GB; optional for MVP
- **Performance:** On-device inference (no API latency)
- **Accuracy:** State-of-the-art LLAMA Guard 2

### Trade-offs

- **Security:** No guardrails = vulnerable to some attacks
- **Complexity:** Two deployment paths

---



## References

- ADR format: https://adr.github.io/
- LangGraph: https://langchain-ai.github.io/langgraph/
- FastAPI: https://fastapi.tiangolo.com/
- Alembic: https://alembic.sqlalchemy.org/
- uv: https://astral.sh/blog/uv/
