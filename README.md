---
title: Career Copilot
emoji: 📚
colorFrom: blue
colorTo: gray
sdk: docker
pinned: false
short_description: AI-powered Career Decision Support
---

# Career Copilot

An **AI-powered career advisor** that provides research-backed guidance through a multi-agent workflow. Ask career questions, and get personalized advice by combining planning, research, analysis, critique, and synthesis stages.

**Key features:**
- 🤖 **Multi-agent workflow** — 5-stage orchestrated reasoning pipeline
- 💾 **Resumable conversations** — Checkpointed state for interrupted sessions
- 🔀 **Multiple LLM providers** — OpenAI, Groq, Google GenAI with fallback chains
- 🛡️ **Safety first** — Llama Prompt Guard 2 for malicious prompt detection
- 🚀 **Real-time streaming** — SSE-based live feedback as workflow progresses
- 🔐 **Secure auth** — JWT tokens, user profiles, conversation history

---

## Quick Start

### Prerequisites

- Python 3.14+ (or 3.10+)
- Node.js 22+
- PostgreSQL or SQLite

### 1. Backend Setup

```bash
cd backend

# Create environment file
cp .env.example .env
# Edit .env with DATABASE_URL, JWT_SECRET, and LLM API keys

# Install dependencies
uv sync --extra transformer-cpu  # CPU (smaller image)
# or: uv sync --extra transformer-gpu  # GPU (CUDA 12.8)

# Run migrations
python scripts/run_migrations.py

# Start server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**API:** `http://127.0.0.1:8000`
- **Docs:** `http://127.0.0.1:8000/docs`
- **Info:** `GET http://127.0.0.1:8000/`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

**Frontend:** `http://localhost:5173`

## Project Structure

```
career_copilot/
├── backend/              # FastAPI, LangGraph, agents, database
├── frontend/             # Vue 3 SPA, TypeScript
├── docs/
│   ├── architecture.md   # System design and data flows
│   └── design-decisions.md # Architecture Decision Records (ADRs)
└── README.md             # This file
```

---

## Documentation

- **[Architecture](docs/architecture.md)** — System design, components, data flow
- **[Design Decisions](docs/design-decisions.md)** — Why we built it this way (ADRs)
- **[Backend README](backend/README.md)** — Setup, guardrails, dependency management
- **[Frontend README](frontend/README.md)** — Development, build, deployment

---

## Configuration

Required environment variables:

```bash
DATABASE_URL=postgresql://user:pass@localhost/career_copilot
JWT_SECRET=your-jwt-secret-here

# LLM Keys (use one or multiple)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=...
GOOGLE_API_KEY=...

# Other Keys
TAVILY_API_KEY=...              # Web search
BRAVESEARCH_API_KEY=...
LANGSMITH_API_KEY=...           # Tracing
CORS_ALLOW_ORIGINS=http://localhost:5173
```

Full `.env.example` in `backend/`.

---

## Key Technologies

| Layer | Stack |
|-------|-------|
| **Frontend** | Vue 3, TypeScript, Vite, Pinia |
| **Backend** | FastAPI, uvicorn, SQLAlchemy async |
| **AI/ML** | LangGraph, LangChain, Transformers, PyTorch |
| **Database** | PostgreSQL/SQLite, Alembic |
| **Deployment** | Docker (multi-stage -> huggingface), uv |

---

## Testing

```bash
cd backend
uv sync --extra transformer-cpu --extra test
uv run pytest tests/ -v
```

---

## License

MIT License — see [`LICENSE`](LICENSE)

---

