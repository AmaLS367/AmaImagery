# AmaImagery Documentation (English)

Welcome to the **AmaImagery** documentation. This guide keeps the current repository, runtime, and deployment flows in sync without throwing away the visual structure of the docs.

## 🎯 What is AmaImagery?

AmaImagery is a self-hosted image generation platform built around:

- 🎨 **Text-to-image generation** through the current `/api/v1/images/generate` flow
- 🔄 **Async worker lifecycle** with persisted task state
- 🔌 **Provider abstraction** for `comfyui` and `diffusers`
- 🛡️ **Auth, admin, and moderation surfaces** already present in the backend
- 🌐 **React + Vite frontend** with generation, history, settings, and auth pages
- 🐳 **Docker-based deployment flows** for local and production setups

Planned or not-yet-public features such as editing, upscaling, and resizing stay visible in roadmap/tutorial sections, but they are not documented as shipped public APIs.

## 📚 Documentation Sections

### [🔧 Backend](./backend/README.md)
Current backend architecture, real route surface, providers, queues, repositories, observability, and admin/readiness behavior.

### [🎨 Frontend](./frontend/README.md)
Current React/Vite frontend structure, routes, and integration points.

### [🐳 Docker](./docker/README.md)
Compose files, runtime targets, env templates, and container flows that exist today.

### [🧪 Tests](./tests/README.md)
Backend test strategy, frontend checks, and current validation commands.

### [🤖 Models](./models/README.md)
Current model assets, provider/runtime expectations, and licensing context.

### [🚀 Deployment](./deployment/README.md)
Production-minded deployment notes and provider rollout guidance.

### [📜 Scripts](./scripts/README.md)
Actual shell, PowerShell, and Python helper scripts in the repository.

### [💻 Development](./development/README.md)
Local setup, API + worker flow, and current developer workflow.

### [🔄 Migrations](./migrations/README.md)
Current Alembic migration path and schema evolution notes.

### [🔒 Security](./security/README.md)
Security posture, reporting path, and sensitive runtime surfaces.

### [⚡ Features](./features/README.md)
Current features, provider-specific capabilities, and planned surfaces.

### [🔍 Troubleshooting](./troubleshooting/README.md)
Current operational issues and debugging notes.

### [⚖️ Legal](./legal/README.md)
Project licensing, model licensing, and attribution guidance.

### [📚 Reference](./reference/README.md)
Current endpoints, commands, env variables, and ports.

### [🎓 Tutorials](./tutorials/README.md)
Guided material and planned tutorials. Some entries are roadmap placeholders by design.

## 🚀 Quick Start Guide

### For Developers
1. Read [Development](./development/README.md)
2. Check [Backend](./backend/README.md)
3. Run the quality checks in [Tests](./tests/README.md)

### For Operators / DevOps
1. Review [Docker](./docker/README.md)
2. Follow [Deployment](./deployment/README.md)
3. Use [Provider Rollout](./deployment/provider-rollout.md) when switching runtimes

### For API Users
1. Read [Reference](./reference/README.md)
2. Review [Backend](./backend/README.md)
3. Check [Troubleshooting](./troubleshooting/README.md) if your environment differs from the documented happy path

## 🏗️ Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │◄────►│    Backend   │◄────►│ PostgreSQL  │
│   (React)   │      │   (FastAPI)  │      │ lifecycle   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Worker +    │
                     │  Providers   │
                     └──────────────┘
```

The current runtime truth is:

- PostgreSQL stores generation lifecycle state
- Redis is queue/rate-limit infrastructure, not the primary source of task truth
- `comfyui` and `diffusers` are the real provider modes
- admin pages live under `/admin/*`

## 📦 Technology Stack

**Backend:**
- FastAPI
- Python 3.11+
- PostgreSQL
- Redis
- SQLAlchemy + Alembic

**Frontend:**
- React + TypeScript
- Vite
- Tailwind CSS
- i18next

**Infrastructure:**
- Docker & Docker Compose
- Nginx
- Async generation worker
- Optional local Diffusers runtime or external ComfyUI runtime

## 🔗 Quick Links

- [Development Guide](./development/README.md)
- [Reference](./reference/README.md)
- [Docker Setup](./docker/README.md)
- [Contributing](../../CONTRIBUTING.md)
- [Troubleshooting](./troubleshooting/README.md)

## 📞 Getting Help

- Check [Troubleshooting](./troubleshooting/README.md)
- Review the current section README for your area
- Use roadmap/tutorial pages as planning context, not as proof that a public API already exists

## 📄 License

This project uses multiple licenses. See [Legal](./legal/README.md) for details:

- application code licensing at the repository root
- model and dataset obligations under `models/`, `NOTICE.txt`, and `ATTRIBUTIONS.md`

---

**Version:** 0.1.0 | **Last Updated:** March 15, 2026
