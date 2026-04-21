# Career Copilot

Python agent backend and Vue frontend for a chat-based career advisor (switches, skill gaps, offers, planning).

## Layout

- `backend/app/` — FastAPI-style layout: `core/`, `config/`, `agents/`, `tools/`, `pipeline.py`, `schema/` (shared schemas).
- `frontend/` — Vue 3 SPA (TypeScript, Vue Router, Pinia).

## Backend

```
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

Copy `backend/.env.example` to `backend/.env` when you wire APIs.

### Backend tests

```
cd backend
uv sync --extra test
uv run pytest tests/ -q
```

Tests use a temporary SQLite file, a FastAPI app **without** the production lifespan (no Hugging Face prompt guard load), and stubbed password hashing so tests do not run Argon2 work.

## Frontend

```
cd frontend
npm install
npm run dev
```

Vite proxies `/api/*` to `http://127.0.0.1:8000` in dev (see `frontend/vite.config.ts`). Run the backend on port **8000** or set `VITE_API_BASE_URL` in `frontend/.env` to your API origin. Ensure backend `CORS_ALLOW_ORIGINS` includes your Vite URL (e.g. `http://localhost:5173`) if you use a full URL instead of the proxy.
