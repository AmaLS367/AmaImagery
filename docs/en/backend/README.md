# Backend Documentation

## Overview

The backend is built with **FastAPI** and Python. Its current public surface is centered on image generation, auth, user settings/history, moderation, file delivery, and admin/readiness flows.

## Key Components

### 🔌 API Layer
- FastAPI route tree under `/api/v1/*`
- JWT-based auth flows
- request validation and rate limiting
- OpenAPI docs via the app docs route when enabled

### 🧠 Provider Runtime
- provider abstraction for image generation
- support for `comfyui` and `diffusers`
- provider readiness and failure tracking
- see [Providers](./providers.md)

### 📦 Queue and Workers
- asynchronous generation queue
- separate worker process for heavy generation tasks
- PostgreSQL as lifecycle source of truth
- Redis as queue/rate-limit infrastructure when enabled
- see [Queue and Workers](./queue-and-workers.md)

### 📋 Application Layer
- use cases for business orchestration
- command/result pattern around generation and status flows
- see [Application Layer](./application.md)

### 🗄️ Data Layer
- PostgreSQL with async SQLAlchemy
- Alembic migrations
- repository pattern + unit of work
- see [Repositories and Unit of Work](./repositories.md)

### ⚡ Concurrency Model
- async ORM and async API handlers
- worker-based execution for long-running generation
- see [Concurrency Model](./concurrency.md)

### 🛡️ Security & Safety
- prompt hygiene support
- NSFW moderation routes
- input validation and security middleware

### 📊 Observability
- structured logging
- domain events
- feature flags
- repo-side metrics modules
- note: a public `/metrics` endpoint is not mounted by default
- see [Observability](./observability.md)

## Documentation Sections

- [Providers](./providers.md) - Provider abstraction layer
- [Admin and Readiness](./admin-and-readiness.md) - Admin access, liveness, readiness, lifecycle contract
- [Queue and Workers](./queue-and-workers.md) - Task queue and worker architecture
- [Application Layer](./application.md) - Use cases and orchestration
- [Repositories and Unit of Work](./repositories.md) - Data access and transactions
- [Concurrency Model](./concurrency.md) - Async and worker execution model
- [Observability](./observability.md) - Errors, events, metrics modules, feature flags

### 🚧 Planned Deep-Dive Pages

- Architecture page — Coming soon
- API sub-tree docs — Coming soon
- Core modules deep-dive — Coming soon
- Services deep-dive — Coming soon
- Inference deep-dive — Coming soon
- Database deep-dive — Coming soon
- Middleware deep-dive — Coming soon
- Configuration deep-dive — Coming soon

## Quick Start

See [Development](../development/README.md) for installation and local run instructions.

## Technology Stack

- **Framework:** FastAPI
- **Python:** 3.11+
- **Database:** PostgreSQL + SQLAlchemy
- **Queue / limits:** Redis
- **Migrations:** Alembic
- **Auth:** JWT / cookies
- **ML runtime:** provider-based `comfyui` or `diffusers`
