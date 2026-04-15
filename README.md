# Career Copilot

Chat-based agentic career advisor: career switches, skill gaps, offer evaluation, and path planning.

## Layout

- `app/core/` — startup (`init_app`).
- `app/config/` — settings (`get_settings`).
- `app/agents/` — planner, research, analyst, critic, synthesizer, feedback (stubs for LLM wiring).
- `app/tools/` — research tool hooks (stubs).
- `app/pipeline.py` — default agent order for one user turn.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Try the stub pipeline

```bash
python -m app.main
```

## Environment

Copy `.env.example` to `.env` when you wire APIs.
