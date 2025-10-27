# Registration Demo Dockerfile
FROM ghcr.io/astral-sh/uv:0.9-python3.13-bookworm-slim AS builder

ARG USER=servicekit UID=10001
RUN useradd -u ${UID} -m -s /bin/bash ${USER}

# UV configuration for better build performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy parent servicekit project (needed as path dependency)
COPY pyproject.toml uv.lock README.md /app/
COPY src /app/src/

# Copy registration example
COPY examples/registration /app/examples/registration

# Install dependencies from registration example directly in /app
WORKDIR /app/examples/registration
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Cleanup Python cache files
RUN find .venv -type d -name '__pycache__' -prune -exec rm -rf {} + && \
    find .venv -type f -name '*.py[co]' -delete || true

# ---- runtime ----
FROM python:3.13-slim AS runtime

# OCI labels for container metadata
LABEL org.opencontainers.image.title="Servicekit Registration Demo"
LABEL org.opencontainers.image.description="Service registration demo with orchestrator"
LABEL org.opencontainers.image.vendor="Servicekit"
LABEL org.opencontainers.image.source="https://github.com/winterop-com/servicekit"

WORKDIR /app

ARG USER=servicekit UID=10001
RUN useradd -u ${UID} -m -s /bin/bash ${USER}

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ca-certificates tini && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy entire app directory including venv and source from builder
COPY --from=builder --chown=${USER}:${USER} /app /app

ENV VIRTUAL_ENV=/app/examples/registration/.venv
ENV PATH=/app/examples/registration/.venv/bin:${PATH}
WORKDIR /app/examples/registration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1

# Server configuration
ENV PORT=8000
ENV TIMEOUT=60
ENV GRACEFUL_TIMEOUT=30
ENV KEEPALIVE=5
ENV FORWARDED_ALLOW_IPS="*"

# Worker configuration
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=200

# Logging configuration
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO

USER ${USER}
EXPOSE 8000

# Health check to verify the API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health').read()" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
# Use uvicorn directly for reliable lifespan execution (required for registration)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---- orchestrator ----
FROM runtime AS orchestrator

# Override healthcheck for orchestrator (port 9000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/health').read()" || exit 1

EXPOSE 9000

# Run orchestrator with uvicorn (single worker for in-memory registry)
CMD ["uvicorn", "orchestrator:app", "--host", "0.0.0.0", "--port", "9000"]
