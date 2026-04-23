# Backend

FastAPI service with LangGraph multi-agent workflow, database persistence, and JWT authentication.

## Quick Start

### Prerequisites

- Python 3.14+ (or 3.10+)
- PostgreSQL or SQLite
- `uv` package manager

### Setup

```bash
cd backend

# 1. Create environment file
cp .env.example .env
# Edit .env with your settings (see Configuration section)

# 2. Install dependencies
uv sync --extra transformer-cpu  # CPU (smaller)
# or: uv sync --extra transformer-gpu  # GPU (CUDA 12.8)

# 3. Run database migrations
python scripts/run_migrations.py

# 4. Start development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**API available at:**
- **Interactive docs:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **API info:** GET http://127.0.0.1:8000/

---

## Configuration

### Environment Variables

Required:
```bash
DATABASE_URL=postgresql://user:pass@localhost/career_copilot
JWT_SECRET=your-jwt-secret-here
```

Optional:
```bash
# LLM Keys (use one or multiple for fallback)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=...
GOOGLE_API_KEY=...

# Search & Tracing
TAVILY_API_KEY=...
LANGSMITH_API_KEY=...

# API Settings
DEBUG=true
LOG_LEVEL=INFO
CORS_ALLOW_ORIGINS=http://localhost:5173
PORT=8000
```

### Database Setup

**PostgreSQL (Production):**
```bash
createdb career_copilot
export DATABASE_URL=postgresql://user:pass@localhost/career_copilot
python scripts/run_migrations.py
```

**SQLite (Development/Testing):**
```bash
export DATABASE_URL=sqlite:///./career_copilot.db
python scripts/run_migrations.py
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── pipeline.py             # LangGraph workflow orchestration
│   │
│   ├── api/
│   │   ├── api.py              # Router composition
│   │   ├── endpoints/
│   │   │   ├── auth.py         # Login, register, JWT
│   │   │   ├── health.py       # Health check
│   │   │   ├── profile.py      # User profile CRUD
│   │   │   └── workflow.py     # Workflow start + stream
│   │   └── deps.py             # Dependency injection
│   │
│   ├── agents/                 # LangGraph agent nodes
│   │   ├── planner.py
│   │   ├── researcher.py
│   │   ├── analyst.py
│   │   ├── critic.py
│   │   └── synthesizer.py
│   │
│   ├── graph/
│   │   ├── career_graph.py     # LangGraph workflow definition
│   │   ├── checkpoint.py       # Checkpoint management
│   │   ├── message_history.py
│   │   ├── feedback_markers.py
│   │   └── agent_invoke.py
│   │
│   ├── guardrails/
│   │   ├── input_size.py       # Max prompt size validation
│   │   └── prompt_guard.py     # Llama Prompt Guard 2 (optional)
│   │
│   ├── llm/
│   │   └── providers.py        # Multi-provider LLM setup
│   │
│   ├── config/
│   │   ├── settings.py         # App settings
│   │   ├── agents.py           # Agent configs
│   │   ├── app_settings.py
│   │   ├── rate_limits.py
│   │   ├── workflow.py
│   │   └── prompt_guard_config.py
│   │
│   ├── core/
│   │   ├── bootstrap.py        # App initialization
│   │   ├── logging_config.py
│   │   ├── rate_limit.py
│   │   ├── request_logging.py
│   │   ├── request_identity.py
│   │   ├── retry_policy.py
│   │   └── agent_runtime.py
│   │
│   ├── db/
│   │   └── session.py          # SQLAlchemy async session
│   │
│   ├── models/
│   │   ├── base.py             # Base ORM model
│   │   ├── user.py
│   │   ├── user_profile.py
│   │   └── ... (other models)
│   │
│   ├── schema/
│   │   ├── auth.py             # Pydantic request/response models
│   │   ├── profile.py
│   │   ├── workflow.py
│   │   ├── agent_outputs.py
│   │   └── search.py
│   │
│   ├── services/
│   │   ├── auth.py             # Auth logic
│   │   ├── profile.py          # Profile service
│   │   ├── mail.py             # Email service
│   │   └── ... (other services)
│   │
│   └── tools/                  # Agent tools (web search, etc.)
│
├── database/                   # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── scripts/
│   ├── run_migrations.py       # Apply Alembic migrations
│   ├── generate_graph_image.py # Export workflow diagram
│   └── ... (other utilities)
│
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── app_factory.py
│   ├── test_auth_api.py
│   ├── test_profile_api.py
│   ├── test_workflow_api.py
│   ├── test_guardrails_input_size.py
│   └── ... (other tests)
│
├── logs/                       # Application logs
│
├── .env.example                # Environment template
├── .dockerignore
├── pyproject.toml              # uv dependencies
├── uv.lock                     # Lock file (reproducible builds)
├── alembic.ini                 # Alembic config
└── README.md                   # This file
```

---

## API Endpoints

### Authentication

```
POST /auth/register
  Body: {"email": "user@example.com", "password": "..."}
  Response: {"user_id": "...", "access_token": "..."}

POST /auth/login
  Body: {"email": "user@example.com", "password": "..."}
  Response: {"access_token": "..."}
```

### Health

```
GET /health
  Response: {"status": "ok", "db": "connected"}
```

### Profile

```
GET /profile
  Headers: {"Authorization": "Bearer <token>"}
  Response: {"user_id": "...", "email": "...", ...}

PUT /profile
  Headers: {"Authorization": "Bearer <token>"}
  Body: {"preferences": {...}, ...}
  Response: {"user_id": "...", ...}
```

### Workflow

```
POST /workflow/start
  Headers: {"Authorization": "Bearer <token>"}
  Body: {"question": "Should I switch to AI?"}
  Response: {"workflow_id": "...", "status": "processing"}

GET /workflow/{workflow_id}
  Headers: {"Authorization": "Bearer <token>"}
  Content-Type: text/event-stream
  Response: EventSource stream with {"stage": "...", "text": "..."}
```

### Info

```
GET /
  Response: {"name": "Career Copilot", "version": "0.1.0", "endpoints": [...]}
```

---

## Testing

### Run Tests

```bash
uv sync --extra transformer-cpu --extra test
uv run pytest tests/ -v
```

### Test Configuration

- **Database:** Temporary SQLite (`:memory:`)
- **Guardrails:** Stubbed (no model loading)
- **Password hashing:** Fast test implementation (argon2)

### Coverage

```bash
uv run pytest tests/ --cov=app --cov-report=html
```

Open `htmlcov/index.html` to view coverage report.

---

## Deployment

### Docker Build

```bash
# CPU build (default, ~1GB)
docker build -t career-copilot:cpu .

# GPU build (CUDA 12.8, ~4GB)
docker build --build-arg TORCH_VARIANT=transformer-gpu -t career-copilot:gpu .
```

### Docker Run

```bash
docker run -p 7860:7860 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e JWT_SECRET=your-secret \
  -e OPENAI_API_KEY=sk-... \
  career-copilot:cpu
```

### Hugging Face Spaces

1. Create new Space with Docker runtime
2. Set repository secrets:
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `OPENAI_API_KEY` (or other LLM keys)
   - `TAVILY_API_KEY`
3. Dockerfile at repo root will auto-build
4. Space runs at `huggingface.co/spaces/username/career-copilot`

---

## Development Workflow

### Adding a New Endpoint

1. Create schema in `app/schema/`
2. Add route in `app/api/endpoints/`
3. Add service logic in `app/services/`
4. Write tests in `tests/`
5. Update API docs (auto-generated from Pydantic models)

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add user_preferences table"

# Review migration in database/versions/
# Then apply:
python scripts/run_migrations.py
```

### Adding LLM Providers

1. Update `backend/app/llm/providers.py`
2. Add config in `backend/app/config/agents.py`
3. Set API key in `.env`
4. Providers auto-discovered at startup

### Guardrails

**With guardrails:**
```bash
uv sync --extra transformer-cpu
```

---

## Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL...
```

**Fix:** Ensure `DATABASE_URL` is set correctly:
```bash
# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/career_copilot

# SQLite
DATABASE_URL=sqlite:///./career_copilot.db
```

### JWT Secret Not Set

```
RuntimeError: JWT_SECRET is required
```

**Fix:** Add to `.env`:
```bash
JWT_SECRET=your-random-secret-key
```

### Migration Errors

```bash
# Check current migration version
alembic current

# Roll back one migration
alembic downgrade -1

# Upgrade to latest
alembic upgrade head
```

### LLM API Key Issues

Check logs:
```bash
tail -f logs/app.log
```

Ensure key is set in `.env`:
```bash
OPENAI_API_KEY=sk-...
```

---

### Rate Limiting

Adjust in `backend/app/config/rate_limits.py`:
```python
DEFAULT_RATE_LIMIT = "100/minute"  # requests per minute
```

---

## Monitoring & Logging

### Log Files

- `logs/app.log` — Application logs
- `logs/requests.log` — HTTP request logs

### LangSmith Tracing

Set `LANGSMITH_API_KEY` in `.env` to enable automatic LLM call tracing.

### Health Check

```bash
curl http://localhost:8000/health
```

---

## References

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [Architecture Guide](../docs/architecture.md)
- [Design Decisions](../docs/design-decisions.md)
