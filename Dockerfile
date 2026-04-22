# syntax=docker/dockerfile:1.4
# Multi-stage image: Hugging Face Spaces / Docker Hub + local dev.
# Uses official `uv` builder image with pre-installed uv and build tools.
# CPU PyTorch index avoids pulling CUDA wheels in slim CPU environments.

# Build argument for transformer extra (cpu or gpu)
# Usage: docker build -t career-copilot:gpu --build-arg TORCH_VARIANT=transformer-gpu .
ARG TORCH_VARIANT=transformer-cpu

# =============================================================================
# Stage 1 — build with uv (official uv builder image with build tools)
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

ARG TORCH_VARIANT

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build

# Install build dependencies for compiling packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev

COPY --link backend/pyproject.toml backend/README.md ./
COPY --link backend/app ./app
COPY --link backend/alembic.ini ./
COPY --link backend/database ./database
COPY --link backend/scripts ./scripts

# Use uv to sync dependencies to /opt/venv
# uv automatically selects correct PyTorch index based on --extra (via [tool.uv.sources])
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev \
        --extra ${TORCH_VARIANT}

# =============================================================================
# Stage 2 — minimal runtime (Python 3.14-slim)
# =============================================================================
FROM python:3.14-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV=/opt/venv

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash app

WORKDIR /app

# Copy venv from builder (same path to preserve shebangs)
COPY --from=builder --link /opt/venv /opt/venv

# Copy application files
COPY --from=builder --link /build/alembic.ini ./
COPY --from=builder --link /build/database ./database
COPY --from=builder --link /build/scripts ./scripts
COPY --chown=app:app backend/app ./app

# Create writable directories for logs and SQLite checkpoints
RUN mkdir -p /app/logs /app/.data \
    && chown -R app:app /app/logs /app/.data /app/scripts \
    && chmod -R u+rwX /app/logs /app/.data

USER app

ENV LOG_FILE_DIR=/app/logs \
    GRAPH_CHECKPOINT_SQLITE_PATH=/app/.data/langgraph_checkpoints.sqlite

EXPOSE 7860

# Default port 7860, can override via environment: docker run -e PORT=8000
CMD ["/opt/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
