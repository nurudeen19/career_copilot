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

## Frontend

```
cd frontend
npm install
npm run dev
```
