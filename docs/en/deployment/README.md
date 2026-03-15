# Deployment Documentation

## Overview

Deployment guidance for running **AmaImagery** in environments that match the current repository.

## Deployment Options

### 🐳 Docker Deployment (Recommended)
- current primary deployment path
- matches the repository compose files
- easiest way to keep API, worker, database, Redis, and nginx aligned

### ☁️ Cloud / Managed Infrastructure
- possible, but not documented as turnkey in the repo yet
- operator responsibility for translating the Docker/runtime contract

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

For now, this README is the canonical deployment overview.

## Current Production Checklist

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
- Docker / Docker Compose if using the documented deployment path
- GPU only when your chosen provider/runtime actually needs local GPU execution
- disk space for outputs, logs, and optional local model assets

## Important Notes

- The repository does not currently document a public `/metrics` endpoint as live by default.
- The worker is not optional if you want the documented async generation lifecycle.
- Provider rollout between `comfyui` and `diffusers` is handled through env/config and compose overrides.
