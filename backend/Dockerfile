FROM python:3.12-slim

# System deps for docling (poppler for PDF, libgl for image processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project

# Copy application code
COPY app/ ./app/

# Writable dirs for uploads, SQLite, and model caches. World-writable because
# Hugging Face Spaces runs the container as an arbitrary non-root UID.
ENV HF_HOME=/app/.cache
RUN mkdir -p uploads data .cache && chmod -R 777 uploads data .cache

# HF Spaces expects the app on 7860; compose overrides PORT + command for local dev.
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]