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

# Create directories for persistent data
RUN mkdir -p uploads data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]