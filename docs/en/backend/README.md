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

### 🔌 Provider Layer
- Provider abstraction for image generation
- Pluggable provider architecture
- Support for multiple generation backends
- See [Provider Documentation](./providers.md) for details

### 📦 Queue and Workers
- Asynchronous task queue for image generation
- Background workers for heavy processing
- Task status tracking via Redis
- See [Queue and Workers Documentation](./queue-and-workers.md) for details

### 📋 Application Layer
- Use cases for business scenario orchestration
- Command/Result pattern for clear input/output
- Separation of business logic from API handlers
- See [Application Layer Documentation](./application.md) for details

### 🗄️ Data Layer
- PostgreSQL database with async SQLAlchemy
- Alembic migrations
- Redis for caching and rate limiting
- Repository pattern for data access abstraction
- Unit of Work for transaction management
- See [Repositories and Unit of Work Documentation](./repositories.md) for details

### ⚡ Concurrency Model
- Async ORM for non-blocking database operations
- Task queue for heavy operations
- Background workers for ML inference and processing
- Event loop safety and performance optimization
- See [Concurrency Model Documentation](./concurrency.md) for details

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

### 🔍 Observability
- Structured error handling with domain exceptions
- Comprehensive metrics for providers, queues, and workers
- Feature flags for runtime configuration
- Domain events for decoupled communication
- See [Observability Documentation](./observability.md) for details

## Documentation Sections

- [Architecture](./architecture.md) - System architecture and design
- [API Documentation](./api/overview.md) - Complete API reference
- [Providers](./providers.md) - Provider abstraction layer
- [Queue and Workers](./queue-and-workers.md) - Task queue and worker architecture
- [Application Layer](./application.md) - Use cases and business scenario orchestration
- [Repositories and Unit of Work](./repositories.md) - Data access layer and transaction management
- [Concurrency Model](./concurrency.md) - Async ORM and concurrency architecture
- [Observability](./observability.md) - Error handling, metrics, feature flags, and domain events
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

