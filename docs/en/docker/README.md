# Docker Documentation

## Overview

The application is fully containerized with Docker and Docker Compose, supporting multiple deployment scenarios: local development, CPU-only, and production with GPU.

## Key Features

### 🐳 Multi-Stage Builds
- Optimized Dockerfile for production
- Separate development and production images
- Layer caching for faster builds

### 🎯 Multiple Compose Configurations
- **compose.local.yml** - Local development
- **compose.cpu.yml** - CPU-only deployment
- **compose.prod.yml** - Production with GPU

### 🔧 Services
- Backend (FastAPI)
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

### Local Development
```bash
docker compose -f docker/compose.local.yml up
```

### Production
```bash
docker compose -f docker/compose.prod.yml up -d
```

See [Getting Started](./getting-started.md) for details.

## Requirements

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker (for GPU support)
- 8GB+ RAM (16GB+ recommended)
- 20GB+ disk space

