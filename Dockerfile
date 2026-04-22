# syntax=docker/dockerfile:1
# Multi-stage image: Hugging Face Spaces / Docker Hub + local dev.
# Uses official `uv` builder image for fast, efficient dependency resolution.
# CPU PyTorch index avoids pulling CUDA wheels in slim CPU environments.

# Build args for controlling transformer/torch installation
ARG TORCH_VARIANT=transformer-cpu

# -----------------------------------------------------------------------------
# Stage 1 — build with uv (official uv builder image)
# -----------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:latest AS builder

WORKDIR /build

COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app
COPY backend/alembic.ini ./
COPY backend/database ./database
COPY backend/scripts ./scripts

# Create venv and sync dependencies with uv
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv /opt/venv && \
    uv sync --python /opt/venv/bin/python \
        --extra ${TORCH_VARIANT}

# -----------------------------------------------------------------------------
# Stage 2 — minimal runtime (Python 3.14-slim)
# -----------------------------------------------------------------------------
FROM python:3.14-slim-bookworm AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash app

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}"

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/alembic.ini ./alembic.ini
COPY --from=builder /build/database ./database
COPY --from=builder /build/scripts ./scripts
COPY backend/app ./app

# Writable at runtime (file logs + optional SQLite checkpoints).
RUN mkdir -p /app/logs /app/.data \
    && chown -R app:app /app/logs /app/.data /app/scripts \
    && chmod -R u+rwX /app/logs /app/.data \
    && find /app/scripts -type f -name "*.py" -exec chmod u+r {} \;

USER app

ENV LOG_FILE_DIR=/app/logs \
    GRAPH_CHECKPOINT_SQLITE_PATH=/app/.data/langgraph_checkpoints.sqlite

EXPOSE 7860

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
