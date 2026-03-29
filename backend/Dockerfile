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

# Run the Uvicorn server, binding to 0.0.0.0 so external Azure traffic can reach it
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
