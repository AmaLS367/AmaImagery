# Reference Documentation

## Overview

API endpoints, commands, environment variables, configuration files, and ports.

## Reference Sections

| Section | Status |
|---------|--------|
| API deep-dive pages | 🚧 Coming soon |
| Configuration deep-dive pages | 🚧 Coming soon |
| CLI deep-dive pages | 🚧 Coming soon |
| Env reference expansion | 🚧 Coming soon |
| Glossary | 🚧 Coming soon |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | `POST` | Register a new user |
| `/api/v1/auth/login` | `POST` | User login |
| `/api/v1/auth/logout` | `POST` | Logout |
| `/api/v1/auth/refresh` | `POST` | Refresh token |
| `/api/v1/auth/me` | `GET` | Current user |
| `/api/v1/auth/forgot-password` | `POST` | Start password reset |
| `/api/v1/auth/reset-password` | `POST` | Complete password reset |
| `/api/v1/auth/change-password` | `POST` | Change password while logged in |
| `/api/v1/images/generate` | `POST` | Submit a generation job |
| `/api/v1/images/status/{task_id}` | `GET` | Poll generation status |
| `/api/v1/users/me/settings` | `GET`, `PATCH` | Read/update user settings |
| `/api/v1/users/me/generations` | `GET` | List generation history |
| `/api/v1/users/me/hygiene-mode` | `GET`, `PATCH` | Read/update hygiene mode |
| `/api/v1/file` | `GET` | Download signed artifact |
| `/api/v1/nsfw/users/me/nsfw` | `PATCH` | Toggle NSFW preference |
| `/api/v1/nsfw/check` | `POST` | Check moderation rules |
| `/api/v1/nsfw/rules` | `GET` | Inspect loaded rules |
| `/api/v1/nsfw/reload` | `POST` | Reload rule cache |
| `/api/v1/health` | `GET` | Liveness |
| `/api/v1/healthz` | `GET` | Readiness |
| `/admin/` | `GET` | Admin landing page |

## Key Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Main database connection string |
| `REDIS_URL` | Redis connection string for queue/rate limiting |
| `SECRET_KEY` | Security-critical application secret |
| `FRONTEND_ORIGIN` | Frontend origin for browser and email flows |
| `PROVIDERS_ENABLED` | Enabled provider list |
| `PROVIDERS_DEFAULT_NAME` | Default provider name |
| `MODEL_ID` | Local model path or identifier |
| `COMFYUI_BASE_URL` | ComfyUI HTTP endpoint |
| `COMFYUI_WEBSOCKET_URL` | ComfyUI websocket endpoint |
| `NO_REDIS` | Redis-off mode for local/test flows |
| `NO_NETWORK` | Network guard toggle |
| `REFRESH_COOKIE_SECURE` | Secure cookie toggle |
| `FILE_SIGNING_ENABLED` | Signed file delivery toggle |

## Common Commands

```bash
# Backend
python run.py
python -m app.entrypoints.generation_worker
alembic upgrade head
pytest -q
python -m ruff check app tests
python -m mypy app

# Frontend
cd frontend
npm ci
npm run dev
npm run typecheck
npm run build

# Docker
docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
docker compose --env-file docker/.env.docker -f docker/compose.local.yml -f docker/compose.local.diffusers.yml up -d --build
docker compose --env-file docker/.env.prod -f docker/compose.prod.yml up -d --build
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.env.example` | App env example |
| `alembic.ini` | Alembic configuration |
| `docker/.env.docker.example` | Local Docker env example |
| `docker/.env.verify.comfyui.example` | Verification profile for ComfyUI |
| `docker/.env.verify.diffusers.example` | Verification profile for Diffusers |
| `docker/compose.*.yml` | Compose configurations |
| `docker/nginx.conf` | Nginx config |
| `frontend/vite.config.ts` | Frontend build/dev config |

## Port Reference

| Service | Port | Description |
|---------|------|-------------|
| Backend API | `8000` | FastAPI application |
| Frontend Dev | `5173` | Vite dev server |
| PostgreSQL | `5432` | Database |
| Redis | `6379` | Queue / rate limit backend |
| Nginx | `80` / `443` / `8080` | Reverse proxy depending on stack |

No public `/metrics` endpoint is mounted by default.
