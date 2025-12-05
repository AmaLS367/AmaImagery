# Backend Documentation

## Overview

The backend is built with **FastAPI** and Python, providing a robust REST API for image generation, editing, and management. It includes ML inference pipeline, database management, authentication, and comprehensive monitoring.

## Key Components

### 🔌 API Layer
- RESTful API with FastAPI
- JWT-based authentication
- Rate limiting and request validation
- Auto-generated OpenAPI documentation

### 🧠 Inference Pipeline
- Stable Diffusion 1.5 integration
- Custom models (AmaFusion, DreamShaper)
- IP-Adapter for image conditioning
- Optimized CUDA inference

### 🗄️ Data Layer
- PostgreSQL database with SQLAlchemy
- Alembic migrations
- Redis for caching and rate limiting

### 🛡️ Security & Safety
- Prompt hygiene system
- NSFW content filtering
- Input validation
- Network security (net_guard)

### 📊 Monitoring
- Prometheus metrics
- Structured logging
- GPU monitoring
- Performance tracking

## Documentation Sections

- [Architecture](./architecture.md) - System architecture and design
- [API Documentation](./api/overview.md) - Complete API reference
- [Core Modules](./core/) - Security, logging, errors, limits
- [Services](./services/) - Business logic services
- [Inference](./inference/) - ML inference pipeline
- [Prompt Hygiene](./prompt-hygiene/) - Prompt validation system
- [Database](./database/) - Database schema and models
- [Middleware](./middleware/) - Request processing middleware
- [Monitoring](./monitoring/) - Metrics and logging
- [Configuration](./configuration.md) - Backend configuration

## Quick Start

See [Development Setup](../development/getting-started.md) for installation instructions.

## Technology Stack

- **Framework:** FastAPI 0.116.1
- **Python:** 3.11+
- **ML:** PyTorch 2.2.2, Diffusers 0.29.2
- **Database:** PostgreSQL, SQLAlchemy 2.0
- **Cache:** Redis 5.0
- **Auth:** JWT (PyJWT)
- **Validation:** Pydantic 2.11

