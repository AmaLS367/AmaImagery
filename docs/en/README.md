# AI Image Generator Documentation (English)

Welcome to the **AI Image Generator** documentation! This comprehensive guide covers all aspects of the system, from setup to deployment.

## 🎯 What is AI Image Generator?

AI Image Generator is a powerful, self-hosted image generation platform based on Stable Diffusion. It features:

- 🎨 **High-quality image generation** with Stable Diffusion 1.5
- ✏️ **Image editing** and manipulation capabilities
- 🔍 **Upscaling** for enhanced resolution
- 🛡️ **Built-in safety features** and content moderation
- 🔒 **Enterprise-grade security** with JWT authentication
- 📊 **Monitoring and metrics** with Prometheus
- 🌐 **Modern web interface** with React
- 🐳 **Docker deployment** ready

## 📚 Documentation Sections

### [🔧 Backend](./backend/README.md)
Complete backend documentation including FastAPI, API endpoints, services, database, and ML inference pipeline.

### [🎨 Frontend](./frontend/README.md)
Frontend documentation covering React components, state management, styling, and API integration.

### [🐳 Docker](./docker/README.md)
Docker and containerization documentation including Docker Compose configurations and deployment.

### [🧪 Tests](./tests/README.md)
Testing documentation including unit tests, integration tests, E2E tests, and testing best practices.

### [🤖 Models](./models/README.md)
ML models documentation covering Stable Diffusion, AmaFusion, DreamShaper, VAE, and IP-Adapter.

### [🚀 Deployment](./deployment/README.md)
Production deployment guides including environment setup, cloud deployment, and maintenance.

### [📜 Scripts](./scripts/README.md)
Documentation for bootstrap, build, migration, and utility scripts.

### [💻 Development](./development/README.md)
Developer guides including setup, project structure, coding standards, and contributing guidelines.

### [🔄 Migrations](./migrations/README.md)
Refactoring and migration notes documenting architectural changes and upgrade guides.

### [🔒 Security](./security/README.md)
Security documentation covering authentication, authorization, rate limiting, and best practices.

### [⚡ Features](./features/README.md)
Feature documentation explaining image generation, editing, upscaling, and content moderation.

### [🔍 Troubleshooting](./troubleshooting/README.md)
Common issues, error codes, and solutions for GPU, memory, and performance problems.

### [⚖️ Legal](./legal/README.md)
Legal information including licenses, model licenses, data sources, and usage restrictions.

### [📚 Reference](./reference/README.md)
Quick reference for API, configuration, CLI commands, environment variables, and glossary.

### [🎓 Tutorials](./tutorials/README.md)
Step-by-step tutorials for common tasks and advanced features.

## 🚀 Quick Start Guide

### For Developers
1. Read [Getting Started](./development/getting-started.md)
2. Set up your [Development Environment](./development/setup/windows.md)
3. Understand the [Project Structure](./development/project-structure.md)
4. Learn about [Testing](./tests/README.md)

### For DevOps
1. Review [System Requirements](./deployment/requirements.md)
2. Follow [Docker Deployment Guide](./docker/getting-started.md)
3. Configure [Environment Variables](./deployment/environment/environment-variables.md)
4. Set up [Monitoring](./deployment/production/monitoring.md)

### For API Users
1. Read [API Overview](./backend/api/overview.md)
2. Learn about [Authentication](./backend/api/authentication.md)
3. Explore [API Endpoints](./backend/api/endpoints/images.md)
4. Check [API Examples](./backend/api/examples.md)

## 🏗️ Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │◄────►│    Backend   │◄────►│  Database   │
│   (React)   │      │   (FastAPI)  │      │ (PostgreSQL)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   ML Models  │
                     │ (Stable Diff)│
                     └──────────────┘
```

See [Architecture Documentation](./backend/architecture.md) for details.

## 📦 Technology Stack

**Backend:**
- FastAPI 0.116.1
- Python 3.11+
- PyTorch 2.2.2
- Diffusers 0.29.2
- PostgreSQL
- Redis

**Frontend:**
- React + TypeScript
- Vite
- Tailwind CSS
- i18next (internationalization)

**Infrastructure:**
- Docker & Docker Compose
- Nginx
- Prometheus metrics
- Alembic migrations

## 🔗 Quick Links

- [Installation Guide](./development/getting-started.md)
- [API Documentation](./backend/api/overview.md)
- [Docker Setup](./docker/getting-started.md)
- [Contributing](../../CONTRIBUTING.md)
- [Troubleshooting](./troubleshooting/common-issues.md)

## 📞 Getting Help

- Check [Troubleshooting](./troubleshooting/README.md) for common issues
- Review [Error Codes](./troubleshooting/error-codes.md)
- See [FAQ](./troubleshooting/common-issues.md)

## 📄 License

This project uses multiple licenses. See [Legal](./legal/README.md) for details:
- Code: See project LICENSE
- Stable Diffusion models: CreativeML Open RAIL-M
- VAE: MIT License

---

**Version:** 0.1.0 | **Last Updated:** March 11, 2026

