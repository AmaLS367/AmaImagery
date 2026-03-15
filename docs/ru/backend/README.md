# Документация бэкенда

## Обзор

Бэкенд построен на **FastAPI** и Python. Его текущая публичная поверхность сосредоточена на генерации изображений, auth, пользовательских настройках/истории, moderation, file delivery и admin/readiness flow.

## Ключевые компоненты

### 🔌 API слой
- FastAPI route tree под `/api/v1/*`
- JWT-based auth flows
- валидация запросов и rate limiting
- OpenAPI docs через docs route приложения, когда она включена

### 🧠 Provider Runtime
- абстракция provider-ов для генерации изображений
- поддержка `comfyui` и `diffusers`
- tracking readiness и ошибок provider-а
- см. [Providers](./providers.md)

### 📦 Очередь и воркеры
- асинхронная очередь генерации
- отдельный worker process для тяжёлых generation tasks
- PostgreSQL как источник истины для lifecycle state
- Redis как инфраструктура очереди и лимитов, когда он включён
- см. [Queue and Workers](./queue-and-workers.md)

### 📋 Слой приложения
- use cases для бизнес-оркестрации
- command/result pattern вокруг generation и status flow
- см. [Application Layer](./application.md)

### 🗄️ Слой данных
- PostgreSQL с async SQLAlchemy
- миграции Alembic
- repository pattern + unit of work
- см. [Repositories and Unit of Work](./repositories.md)

### ⚡ Модель конкурентности
- async ORM и async API handlers
- worker-based выполнение для long-running generation
- см. [Concurrency Model](./concurrency.md)

### 🛡️ Безопасность и защита
- поддержка prompt hygiene
- NSFW moderation routes
- валидация ввода и security middleware

### 📊 Наблюдаемость
- структурированное логирование
- доменные события
- feature flags
- metrics modules внутри репозитория
- важно: публичный `/metrics` endpoint по умолчанию не смонтирован
- см. [Observability](./observability.md)

## Разделы документации

- [Providers](./providers.md) - слой абстракции provider-ов
- [Queue and Workers](./queue-and-workers.md) - архитектура очереди и worker-а
- [Application Layer](./application.md) - use cases и orchestration
- [Repositories and Unit of Work](./repositories.md) - доступ к данным и транзакции
- [Concurrency Model](./concurrency.md) - async и worker execution model
- [Observability](./observability.md) - ошибки, события, metrics modules, feature flags

### 🚧 Planned Deep-Dive Pages

- Architecture page — Coming soon
- API sub-tree docs — Coming soon
- Core modules deep-dive — Coming soon
- Services deep-dive — Coming soon
- Inference deep-dive — Coming soon
- Database deep-dive — Coming soon
- Middleware deep-dive — Coming soon
- Configuration deep-dive — Coming soon

## Быстрый старт

См. [Development](../development/README.md) для установки и локального запуска.

## Технологический стек

- **Framework:** FastAPI
- **Python:** 3.11+
- **База данных:** PostgreSQL + SQLAlchemy
- **Очередь / лимиты:** Redis
- **Миграции:** Alembic
- **Auth:** JWT / cookies
- **ML runtime:** provider-based `comfyui` или `diffusers`
