---
title: Career Copilot
emoji: 📚
colorFrom: blue
colorTo: gray
sdk: docker
pinned: false
short_description: AI-powered Career Decision Support
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
# Career Copilot

Monorepo for a **chat-based career advisor**: research-backed guidance (planning → research → analysis → critique → synthesis), user profiles, and authenticated API access. The backend is a **FastAPI** service with a **LangGraph** workflow; the client is a **Vue 3** SPA.

## Current status (April 2026)

| Area | State |
|------|--------|
| **API** | Auth (JWT), profile CRUD, workflow **SSE** stream, health checks, rate limits, optional LangSmith tracing |
| **Workflow** | Checkpointed LangGraph: validation → planner → (research \| user handoff) → analyst → critic → synthesizer; **thumbs-down** re-enters planner with a short marker + clarifying flow |
| **LLM** | Per-agent provider keys (OpenAI, Groq, OpenRouter, Google); optional **primary + fallback** chain via LangChain `with_fallbacks` where supported |
| **Guardrails** | Input size limits + **Llama Prompt Guard 2** (softmax P(malicious) vs threshold); `transformers` / `torch` are **optional extras** (`transformers-cpu` / `transformers-gpu`) — see `backend/README.md` |
| **Persistence** | PostgreSQL (Alembic migrations) or SQLite for tests; LangGraph Postgres or SQLite checkpointer |
| **Frontend** | Dashboard chat (workflow stream), profile modal, auth flows, markdown rendering |
| **Deploy** | Multi-stage **`backend/Dockerfile`** (CPU torch index) suitable for Docker / Hugging Face Spaces; tuning continues separately |

Documentation for **why** things are built a certain way lives under **`docs/design-decisions/`**. **System shape and data flow** are summarized under **`docs/architecture/`**.

## Repository layout

```
career_copilot/
├── backend/           # FastAPI app, LangGraph, agents, Alembic, Dockerfile
│   ├── app/           # api/, agents/, config/, graph/, guardrails/, schema/, services/, tools/
│   ├── database/      # Alembic versions
│   ├── scripts/       # Migrations helpers, graph export, etc.
│   ├── tests/
│   ├── Dockerfile
│   └── README.md      # Install extras, Docker, prompt guard
├── frontend/          # Vue 3 + Vite + TypeScript
├── docs/
│   ├── design-decisions/   # ADRs and rationale (add files as you go)
│   └── architecture/     # High-level diagrams and flow descriptions
└── README.md          # This file
```

## Backend

1. Copy `backend/.env.example` → `backend/.env` and set at least `DATABASE_URL`, `JWT_SECRET`, and LLM / search keys as needed.
2. Install with **`pyproject.toml`** (prompt guard needs a **transformers** extra + CPU/GPU torch index — details in **`backend/README.md`**).

```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
pip install --extra-index-url https://download.pytorch.org/whl/cpu -e ".[transformers-cpu]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run DB migrations when the schema changes (`backend/scripts/run_migrations.py` or Alembic per your ops).

**Docker / Spaces:** from `backend/`: `docker build -t career-copilot-backend .` — see `backend/README.md`.

### Backend tests

```bash
cd backend
uv sync --extra test --extra transformers-cpu
uv run pytest tests/ -q
```

Tests use a temp SQLite DB and a FastAPI app **without** the full production lifespan (no prompt-guard model load on every test). Stubbed password hashing avoids heavy Argon2 work.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api/*` to `http://127.0.0.1:8000` by default (`frontend/vite.config.ts`). Point `VITE_API_BASE_URL` at your API if needed. Ensure `CORS_ALLOW_ORIGINS` on the backend includes your dev origin (e.g. `http://localhost:5173`).

## Documentation

| Path | Purpose |
|------|--------|
| [`docs/design-decisions/`](docs/design-decisions/) | Record of product/engineering choices (ADRs, trade-offs, rejected options). |
| [`docs/architecture/`](docs/architecture/) | How components connect: graph, agents, auth, streaming, data stores. |

## License / contributing

Add a `LICENSE` and contribution guidelines when you open the repo publicly.
