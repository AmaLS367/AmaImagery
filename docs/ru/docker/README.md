# Документация Docker

## Обзор

Приложение полностью контейнеризовано с Docker и Docker Compose, с явным разделением между лёгкой orchestration-схемой для ComfyUI и локальным ML runtime для Diffusers.

## Ключевые возможности

### 🐳 Runtime Targets
- `runtime-core` для API и ComfyUI orchestration без локальных ML-зависимостей
- `runtime-ml` для локальных Diffusers-воркеров и API-инстансов, которым нужно поднимать Diffusers
- Кэширование слоёв для быстрой пересборки

### 🎯 Несколько конфигураций Compose
- **compose.local.yml** - Локальный ComfyUI-first стек без локального Diffusers runtime
- **compose.local.diffusers.yml** - Локальный override для включения ML runtime
- **compose.prod.yml** - Production ComfyUI-first стек
- **compose.prod.diffusers.yml** - Production override для локального Diffusers runtime

### 🔧 Сервисы
- Backend (FastAPI)
- Frontend (Nginx)
- База данных PostgreSQL
- Кэш Redis
- Обратный прокси Nginx

## Разделы документации

- [Начало работы](./getting-started.md) - Быстрый старт с Docker
- [Конфигурации Compose](./compose/) - Детали Docker Compose
- [Dockerfile](./dockerfile.md) - Объяснение Dockerfile
- [Nginx](./nginx.md) - Конфигурация Nginx
- [Redis](./redis.md) - Redis в Docker
- [PostgreSQL](./postgres.md) - PostgreSQL в Docker
- [Volumes](./volumes.md) - Управление томами
- [Сети](./networking.md) - Сети Docker
- [Устранение неполадок](./troubleshooting.md) - Частые проблемы Docker

## Быстрый старт

### Локальная ComfyUI-first разработка
```bash
docker compose -f docker/compose.local.yml up
```

### Локальная разработка с Diffusers
```bash
docker compose -f docker/compose.local.yml -f docker/compose.local.diffusers.yml up
```

### Production ComfyUI-first
```bash
docker compose -f docker/compose.prod.yml up -d
```

### Production с Diffusers
```bash
docker compose -f docker/compose.prod.yml -f docker/compose.prod.diffusers.yml up -d
```

См. [Начало работы](./getting-started.md) для подробностей.

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker (нужен только для локального GPU runtime с Diffusers)
- 8GB+ RAM (16GB+ рекомендуется)
- 20GB+ дискового пространства

