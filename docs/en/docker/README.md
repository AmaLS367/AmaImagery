# Docker Documentation

## Overview

The application is fully containerized with Docker and Docker Compose, with an explicit split between lightweight ComfyUI orchestration and local Diffusers ML runtime.

## Key Features

### 🐳 Runtime Targets
- `runtime-core` for API and ComfyUI orchestration without local ML dependencies
- `runtime-ml` for local Diffusers workers and API instances that must boot Diffusers
- Layer caching for faster rebuilds

### 🎯 Multiple Compose Configurations
- **compose.local.yml** - Local ComfyUI-first stack without local Diffusers runtime
- **compose.local.diffusers.yml** - Local override that enables the ML runtime
- **compose.prod.yml** - Production ComfyUI-first stack
- **compose.prod.diffusers.yml** - Production override for local Diffusers runtime

### 🔧 Services
- Backend (FastAPI)
- Generation Worker (Background task processor)
- Frontend (Nginx)
- PostgreSQL database
- Redis cache
- Nginx reverse proxy

## Documentation Sections

- [Getting Started](./getting-started.md) - Quick start with Docker
- [Compose Configurations](./compose/) - Docker Compose details
- [Dockerfile](./dockerfile.md) - Dockerfile explanation
- [Nginx](./nginx.md) - Nginx configuration
- [Redis](./redis.md) - Redis in Docker
- [PostgreSQL](./postgres.md) - PostgreSQL in Docker
- [Volumes](./volumes.md) - Volume management
- [Networking](./networking.md) - Docker networking
- [Troubleshooting](./troubleshooting.md) - Common Docker issues

## Quick Start

### Local ComfyUI-first Development
```bash
docker compose -f docker/compose.local.yml up
```

This starts all services including the generation worker.

### Local Diffusers Development
```bash
docker compose -f docker/compose.local.yml -f docker/compose.local.diffusers.yml up
```

This adds the local ML runtime on top of the default stack.

### Production ComfyUI-first
```bash
docker compose -f docker/compose.prod.yml up -d
```

This starts all services including the generation worker in detached mode.

### Production Diffusers
```bash
docker compose -f docker/compose.prod.yml -f docker/compose.prod.diffusers.yml up -d
```

### Worker Service

The `generation_worker` service processes image generation tasks from the queue. It:
- Consumes tasks from Redis queue
- Processes generation via providers
- Saves results to database
- Updates task status

See [Queue and Workers Documentation](../backend/queue-and-workers.md) for details.

See [Getting Started](./getting-started.md) for details.

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker (only for local Diffusers GPU runtime)
- 8GB+ RAM (16GB+ recommended)
- 20GB+ disk space

