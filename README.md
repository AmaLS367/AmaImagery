# AmaImagery

> Self-hosted image generation backend and frontend with asynchronous jobs, provider failover, and an operationally visible runtime.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-frontend-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-supported-2496ED.svg)](https://www.docker.com)
[![Ruff](https://img.shields.io/badge/ruff-enabled-FFDB4D.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![MyPy](https://img.shields.io/badge/mypy-enabled-0E6EB8.svg)](https://mypy.readthedocs.io/)

AmaImagery is a self-hosted image generation platform built around a FastAPI backend, a React frontend, and an async worker pipeline. It exposes a single API contract for multiple generation providers and is currently oriented toward `ComfyUI` as the primary runtime, with `Diffusers` support still present in the codebase.

## What It Is

- Async image generation with queue-backed status polling and history
- Provider-aware runtime with health/readiness visibility
- Superuser-only admin panel for users and generations
- Artifact download flow for completed generations
- Docker-based local verification path
- Repo-level linting, typing, and CI quality gates with `ruff` and `mypy`

## Current Status

This repository is actively maintained and suitable for development, staging, and controlled self-hosted deployments.

It is not presented here as a lightweight turnkey appliance:

- the default Docker image is still CUDA-oriented and relatively heavy
- `ComfyUI` is the most realistic end-to-end generation path today
- `Diffusers` remains available, but local model management is still a significant operational concern

That distinction is deliberate. The codebase is moving toward a cleaner production story, but the runtime footprint is still substantial.

## Architecture

AmaImagery is split into a few major parts:

- `app/`: FastAPI application, domain logic, providers, repositories, worker code
- `frontend/`: React client
- `tests/`: unit, integration, worker, security, and performance coverage
- `migrations/`: Alembic migrations
- `docker/`: local compose setup and provider verification environments
- `docs/`: English and Russian documentation trees

The backend lifecycle is centered on:

- API request acceptance
- generation persistence in PostgreSQL
- async job execution through the worker
- provider submission and polling
- artifact persistence and download exposure

## Quick Start

### Docker

```bash
git clone https://github.com/AmaLS367/AmaImagery
cd AmaImagery
docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
```

For provider-specific verification, start from:

- `docker/.env.verify.comfyui.example`
- `docker/.env.verify.diffusers.example`

### Local Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python run.py
python -m app.entrypoints.generation_worker
```

## Verification

Useful checks during local setup:

```bash
python -m ruff check app tests
python -m mypy app
python -m pytest tests -q
```

Operational endpoints:

- `GET /api/v1/health` for liveness plus provider boot summary
- `GET /api/v1/healthz` for generation readiness
- `GET /admin/` for the superuser admin surface

## Documentation

- [Documentation Index](./docs/README.md)
- [English Docs](./docs/en/README.md)
- [Backend Admin and Readiness](./docs/en/backend/admin-and-readiness.md)
- [Provider Rollout Notes](./docs/en/deployment/provider-rollout.md)

Repository-level project docs:

- [Contributing](./CONTRIBUTING.md)
- [Security](./SECURITY.md)
- [Support](./SUPPORT.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Commercial Licensing](./COMMERCIAL_LICENSE.md)

## Licensing

AmaImagery uses dual licensing for the application code:

- Open-source use: `AGPL-3.0-only`
- Commercial use: contact `amalsdev367@gmail.com`

Model weights, datasets, and third-party assets may carry additional obligations. See:

- [LICENSE](./LICENSE)
- [NOTICE.txt](./NOTICE.txt)
- [ATTRIBUTIONS.md](./ATTRIBUTIONS.md)
- [Legal Docs](./docs/en/legal/README.md)

## Support

- Bugs and feature requests: GitHub Issues
- Questions and usage discussion: GitHub Discussions
- Security disclosures: `amalsdev367@gmail.com`
- Commercial licensing: `amalsdev367@gmail.com`
