# Use Astral's official, hyper-optimized uv Python image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set the working directory directly
WORKDIR /app

# System environment variables for leaner builds
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# 1. Copy over the dependency definitions
COPY pyproject.toml uv.lock ./

# 2. Install dependencies FIRST to leverage Docker caching.
RUN uv sync --frozen --no-install-project

# 3. Copy the rest of your application code
COPY . /app

# 4. Final installation sync to seal the environment
RUN uv sync --frozen

# Expose port 80. Azure Web Apps automatically routes incoming HTTP traffic to Port 80 by default.
EXPOSE 80

# Production server: Gunicorn manages worker processes; each worker is a Uvicorn ASGI server.
# WORKERS env var controls concurrency (default 2). Use 2–4 on Azure B-series plans.
# --timeout 120 prevents Gunicorn killing workers during long LLM/yfinance calls.
# Local dev: use `uv run uvicorn main:app --reload --port 8000` instead.
CMD ["sh", "-c", "uv run gunicorn main:app --workers ${WORKERS:-2} --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80 --timeout 120 --access-logfile -"]
