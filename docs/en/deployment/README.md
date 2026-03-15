# Deployment Documentation

## Overview

Deployment guidance for running **AmaImagery**.

## Deployment Options

### 🐳 Docker Deployment (Recommended)
- primary deployment path
- matches the repository compose files
- easiest way to keep API, worker, database, Redis, and nginx aligned

### ☁️ Cloud / Managed Infrastructure
- no turnkey cloud deployment guide is provided
- operators are responsible for adapting the Docker/runtime contract to their infrastructure

### 🖥️ Bare Metal
- possible for advanced operators
- especially relevant when local GPU/Diffusers work is needed

## Documentation Sections

| Topic | Status |
|------|--------|
| Requirements page | 🚧 Coming soon |
| Environment deep-dive | 🚧 Coming soon |
| Production checklist page | 🚧 Coming soon |
| TLS / SSL page | 🚧 Coming soon |
| Monitoring page | 🚧 Coming soon |
| Scaling page | 🚧 Coming soon |
| Cloud guides | 🚧 Coming soon |
| Maintenance playbook | 🚧 Coming soon |
| [Provider Rollout](./provider-rollout.md) | ✅ Available |

## Production Checklist

1. ✅ Prepare a real production env file
2. ✅ Set a strong `SECRET_KEY`
3. ✅ Use PostgreSQL
4. ✅ Configure Redis if Redis-backed queueing is enabled
5. ✅ Build `frontend/dist`
6. ✅ Start API and `generation_worker`
7. ✅ Verify `/api/v1/health` and `/api/v1/healthz`
8. ✅ Run a smoke generation and confirm history/status stay aligned

## Minimum Requirements

- enough CPU/RAM for API + worker + database + provider runtime
- Docker / Docker Compose for the Docker-based deployment
- GPU only when your chosen provider/runtime actually needs local GPU execution
- disk space for outputs, logs, and optional local model assets

## Important Notes

- A public `/metrics` endpoint is not mounted by default.
- The worker is required for the async generation lifecycle.
- Provider rollout between `comfyui` and `diffusers` is handled through env/config and compose overrides.
