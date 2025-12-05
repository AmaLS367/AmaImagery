# Reference Documentation

## Overview

Quick reference documentation for APIs, configuration, CLI commands, environment variables, and terminology.

## Reference Sections

### [📡 API Reference](./api-reference.md)
Complete API endpoint reference with request/response schemas, authentication requirements, and examples.

### [⚙️ Configuration](./configuration.md)
All configuration options for backend, frontend, Docker, and deployment.

### [💻 CLI Commands](./cli-commands.md)
Command-line interface commands for development, deployment, and maintenance.

### [🔧 Environment Variables](./environment-variables.md)
Complete list of environment variables with descriptions, defaults, and examples.

### [📖 Glossary](./glossary.md)
Definitions of terms, acronyms, and concepts used throughout the project.

## Quick Reference

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/refresh` | POST | Refresh token |
| `/api/v1/images/generate` | POST | Generate image |
| `/api/v1/images/edit` | POST | Edit image |
| `/api/v1/images/upscale` | POST | Upscale image |
| `/api/v1/users/me` | GET | Get current user |
| `/health` | GET | Health check |

See [API Reference](./api-reference.md) for complete details.

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `REDIS_URL` | - | Redis connection string |
| `SECRET_KEY` | - | JWT secret key |
| `FRONTEND_ORIGIN` | - | Frontend URL for CORS |
| `CUDA_VRAM_FRACTION` | 0.9 | GPU memory fraction |
| `MAX_WORKERS` | 4 | Worker processes |

See [Environment Variables](./environment-variables.md) for complete list.

### Common CLI Commands

```bash
# Development
python run_dev.py                    # Run dev server
pytest tests/                        # Run tests
alembic upgrade head                # Run migrations

# Docker
docker compose up                   # Start containers
docker compose logs -f backend     # View logs
docker compose down                # Stop containers

# Scripts
./scripts/linux/bootstrap.sh       # Initialize environment
./scripts/linux/migrate.sh         # Run migrations
./scripts/linux/smoketest.sh       # Run smoke tests
```

See [CLI Commands](./cli-commands.md) for complete reference.

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `alembic.ini` | Database migration config |
| `docker/compose.*.yml` | Docker Compose configs |
| `docker/nginx.conf` | Nginx configuration |
| `frontend/vite.config.ts` | Vite build config |
| `pytest.ini` | Test configuration |

## Model Configurations

| File | Purpose |
|------|---------|
| `models/configs/v1-inference.yaml` | Inference config |
| `models/clip-vit-large-patch14/config.json` | CLIP config |
| `models/vae/config.json` | VAE config |

## Port Reference

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI application |
| Frontend Dev | 5173 | Vite dev server |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache/queue |
| Nginx | 80/443 | Reverse proxy |
| Prometheus | 9090 | Metrics (optional) |

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

See [Error Codes](../troubleshooting/error-codes.md) for application-specific codes.

