# Docker Documentation

## Overview

The application is containerized with Docker and Docker Compose, with an explicit split between a lightweight core runtime and a heavier local Diffusers runtime.

## Key Features

### 🐳 Runtime Targets
- `runtime-core` for API and worker without local Diffusers dependencies
- `runtime-ml` for local Diffusers execution
- layer caching for faster rebuilds

### 🎯 Multiple Compose Configurations
- **compose.local.yml** - Local core stack
- **compose.local.diffusers.yml** - Local override that enables the ML runtime
- **compose.prod.yml** - Production-oriented core stack
- **compose.prod.diffusers.yml** - Production override for local Diffusers runtime

### 🔧 Services
- API (`api`)
- Generation Worker (`generation_worker`)
- PostgreSQL
- Redis
- Nginx

## Documentation Sections

| Topic | Status |
|------|--------|
| Getting Started page | 🚧 Coming soon |
| Compose deep-dive pages | 🚧 Coming soon |
| Dockerfile deep-dive | 🚧 Coming soon |
| Nginx deep-dive | 🚧 Coming soon |
| Redis deep-dive | 🚧 Coming soon |
| PostgreSQL deep-dive | 🚧 Coming soon |
| Volumes / networking deep-dive | 🚧 Coming soon |
| [Troubleshooting](../troubleshooting/README.md) | ✅ Available |

## Quick Start

### Local Core Stack
```bash
docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
```

### Local Diffusers Stack
```bash
docker compose --env-file docker/.env.docker -f docker/compose.local.yml -f docker/compose.local.diffusers.yml up -d --build
```

### Production Core Stack
```bash
docker compose --env-file docker/.env.prod -f docker/compose.prod.yml up -d --build
```

### Production Diffusers Stack
```bash
docker compose --env-file docker/.env.prod -f docker/compose.prod.yml -f docker/compose.prod.diffusers.yml up -d --build
```

## Worker Service

The `generation_worker` service processes generation tasks separately from the API:

- consumes queued tasks
- executes generation through the selected provider
- stores artifacts and updates lifecycle state

See [Queue and Workers](../backend/queue-and-workers.md) for details.

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker only if you need local GPU Diffusers runtime
- enough RAM/disk for your chosen runtime and models

## Important Notes

- Build `frontend/dist` before relying on bundled static frontend delivery.
- Copy `docker/.env.docker.example` to `docker/.env.docker` before running the local stack. The verification env files are targeted presets for specific provider profiles.
- A public `/metrics` endpoint is not wired into the app by default.
