# Документация Docker

## Обзор

Приложение полностью контейнеризовано с Docker и Docker Compose, поддерживая несколько сценариев развертывания: локальная разработка, только CPU и production с GPU.

## Ключевые возможности

### 🐳 Многоэтапные сборки
- Оптимизированный Dockerfile для production
- Отдельные образы для разработки и production
- Кэширование слоев для быстрой сборки

### 🎯 Несколько конфигураций Compose
- **compose.local.yml** - Локальная разработка
- **compose.cpu.yml** - Развертывание только на CPU
- **compose.prod.yml** - Production с GPU

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

### Локальная разработка
```bash
docker compose -f docker/compose.local.yml up
```

### Production
```bash
docker compose -f docker/compose.prod.yml up -d
```

См. [Начало работы](./getting-started.md) для подробностей.

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker (для поддержки GPU)
- 8GB+ RAM (16GB+ рекомендуется)
- 20GB+ дискового пространства

