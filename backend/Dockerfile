# Build args for controlling transformer/torch installation
ARG TORCH_VARIANT=transformers-cpu

# -----------------------------------------------------------------------------
# Stage 1 — build with uv (official uv builder image)
# -----------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:latest AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic.ini ./
COPY database ./database
COPY scripts ./scripts

# Set PyTorch index URL based on variant: CPU uses custom index, GPU uses default PyTorch index
RUN if [ "${TORCH_VARIANT}" = "transformers-gpu" ]; then \
        export TORCH_INDEX="https://download.pytorch.org/whl/cu118"; \
    else \
        export TORCH_INDEX="https://download.pytorch.org/whl/cpu"; \
    fi && \
    uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python \
        --extra-index-url ${TORCH_INDEX} \
        ".[${TORCH_VARIANT}]"

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

# Writable at runtime (file logs + optional SQLite checkpoints). ``app`` comes from the venv site-packages.
RUN mkdir -p /app/logs /app/.data \
    && chown -R app:app /app/logs /app/.data /app/scripts \
    && chmod -R u+rwX /app/logs /app/.data \
    && find /app/scripts -type f -name "*.py" -exec chmod u+r {} \;

USER app

ENV LOG_FILE_DIR=/app/logs \
    GRAPH_CHECKPOINT_SQLITE_PATH=/app/.data/langgraph_checkpoints.sqlite

EXPOSE 7860
# Spaces injects PORT; default 7860 for local `docker run -p 7860:7860`
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
