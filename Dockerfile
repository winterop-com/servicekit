# ---- builder ----
FROM ghcr.io/astral-sh/uv:0.9-python3.13-bookworm-slim AS builder
WORKDIR /app

ARG USER=servicekit UID=10001
RUN useradd -u ${UID} -m -s /bin/bash ${USER}

# UV configuration for better build performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV UV_PIP_EXTRA_ARGS="--only-binary=:all:"

# Copy project files needed for wheel build
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install git (needed for some dependencies) and build servicekit wheel
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Build servicekit wheel
RUN uv build

# Create venv and install servicekit wheel (includes gunicorn as dependency)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && \
    uv pip install dist/*.whl

# Cleanup Python cache files
RUN find /app/.venv -type d -name '__pycache__' -prune -exec rm -rf {} + && \
    find /app/.venv -type f -name '*.py[co]' -delete || true

# ---- runtime ----
FROM python:3.13-slim AS runtime

# OCI labels for container metadata
LABEL org.opencontainers.image.title="Servicekit Examples"
LABEL org.opencontainers.image.description="Production examples for Servicekit async SQLAlchemy framework with FastAPI"
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

# Copy venv from builder
COPY --from=builder --chown=${USER}:${USER} /app/.venv /app/.venv

# Copy examples
COPY --chown=${USER}:${USER} examples/ ./examples/
COPY --chown=${USER}:${USER} gunicorn.conf.py ./

ENV VIRTUAL_ENV=/app/.venv
ENV PATH=/app/.venv/bin:${PATH}
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

# Default example to run (can be overridden)
ENV EXAMPLE_MODULE=examples.core_api:app

USER ${USER}
EXPOSE 8000

# Health check to verify the API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health').read()" || exit 1

ENTRYPOINT ["/usr/bin/tini","--"]

CMD ["sh","-c", "\
    effective_cpus() { \
        base=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1); \
        if read -r quota period < /sys/fs/cgroup/cpu.max 2>/dev/null; then \
        if [ \"$quota\" != \"max\" ]; then \
            echo $(( (quota + period - 1) / period )); return; \
        fi; \
        fi; \
        echo \"$base\"; \
    }; \
    : ${FORWARDED_ALLOW_IPS:='*'}; \
    CPUS=$(effective_cpus); \
    : ${WORKERS:=$(( CPUS * 2 + 1 ))}; \
    exec gunicorn -k uvicorn.workers.UvicornWorker ${EXAMPLE_MODULE} \
        --bind 0.0.0.0:${PORT} \
        --workers ${WORKERS} \
        --timeout ${TIMEOUT} \
        --graceful-timeout ${GRACEFUL_TIMEOUT} \
        --keep-alive ${KEEPALIVE} \
        --forwarded-allow-ips=${FORWARDED_ALLOW_IPS} \
        --max-requests ${MAX_REQUESTS} \
        --max-requests-jitter ${MAX_REQUESTS_JITTER} \
        --worker-tmp-dir /dev/shm \
\"]
