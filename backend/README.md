# Career Copilot — backend

FastAPI + LangGraph service.

## Install (local)

Core dependencies only (no Hugging Face prompt guard models):

```bash
pip install -e .
```

With **Llama Prompt Guard** (pick one; `torch` wheels differ by index, not by package name):

**CPU (recommended for Docker / Spaces)**

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cpu -e ".[transformers-cpu]"
```

**GPU (CUDA hosts — use the PyTorch index that matches your CUDA version)**

```bash
pip install -e ".[transformers-gpu]"
```

Run tests:

```bash
pip install -e ".[test,transformers-cpu]" --extra-index-url https://download.pytorch.org/whl/cpu
pytest
```

## Docker

From this directory (`backend/`):

```bash
docker build -t career-copilot-backend .
docker run --rm -p 7860:7860 --env-file .env career-copilot-backend
```

Hugging Face Spaces sets `PORT`; the image defaults to `7860` if unset.

Writable paths in the image: `/app/logs` (file logging), `/app/.data` (SQLite checkpoints when used).
