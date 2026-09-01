# ==============================================================================
# AmaImagery Dockerfile
# Multi-stage, security-hardened, non-root container images for Core and ML targets.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1a: Core Builder
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder-core

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Pre-install dependencies to leverage layer caching
COPY pyproject.toml README.md ./
RUN mkdir -p /build/app \
    && printf "__all__ = []\n" > /build/app/__init__.py \
    && pip install --upgrade pip setuptools wheel \
    && pip install .


# ------------------------------------------------------------------------------
# Stage 1b: Core Runtime (Default target for API and Worker)
# ------------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime-core

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/app/models/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create deterministic non-root system user and group (UID/GID 10001)
RUN groupadd -g 10001 app \
    && useradd -u 10001 -g app -s /bin/bash -m -d /app app

WORKDIR /app

# Copy virtualenv from builder stage
COPY --from=builder-core --chown=app:app /opt/venv /opt/venv

# Prepare writable runtime directories
RUN mkdir -p /app/outputs /app/logs /app/models \
    && chown -R app:app /app

# Copy application source and configuration with proper ownership
COPY --chown=app:app app ./app
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app scripts ./scripts
COPY --chown=app:app alembic.ini run.py pyproject.toml README.md NOTICE.txt LICENSE ./

EXPOSE 8000

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/healthz || exit 1

CMD ["python", "run.py"]


# ------------------------------------------------------------------------------
# Stage 2a: ML / CUDA Builder
# ------------------------------------------------------------------------------
FROM nvidia/cuda:13.3.1-devel-ubuntu22.04 AS builder-ml

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential \
    curl \
    git \
    libffi-dev \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
RUN mkdir -p /build/app \
    && printf "__all__ = []\n" > /build/app/__init__.py \
    && pip install --upgrade pip setuptools wheel \
    && pip install ".[ml]"


# ------------------------------------------------------------------------------
# Stage 2b: ML / CUDA Runtime (Target for standalone GPU diffusers pipeline)
# ------------------------------------------------------------------------------
FROM nvidia/cuda:13.3.1-runtime-ubuntu22.04 AS runtime-ml

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/app/models/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    && rm -rf /var/lib/apt/lists/*

# Create deterministic non-root system user and group (UID/GID 10001)
RUN groupadd -g 10001 app \
    && useradd -u 10001 -g app -s /bin/bash -m -d /app app

WORKDIR /app

# Copy virtualenv from ML builder stage
COPY --from=builder-ml --chown=app:app /opt/venv /opt/venv

# Prepare writable runtime directories
RUN mkdir -p /app/outputs /app/logs /app/models \
    && chown -R app:app /app

# Copy application source and configuration with proper ownership
COPY --chown=app:app app ./app
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app scripts ./scripts
COPY --chown=app:app alembic.ini run.py pyproject.toml README.md NOTICE.txt LICENSE ./

EXPOSE 8000

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/healthz || exit 1

CMD ["python", "run.py"]
