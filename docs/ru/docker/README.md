# Документация Docker

## Обзор

Приложение контейнеризовано через Docker и Docker Compose, с явным разделением между лёгким core runtime и более тяжёлым локальным Diffusers runtime.

## Ключевые возможности

### 🐳 Runtime Targets
- `runtime-core` для API и worker-а без локальных Diffusers зависимостей
- `runtime-ml` для локального Diffusers execution
- кэширование слоёв для более быстрой пересборки

### 🎯 Несколько Compose-конфигураций
- **compose.local.yml** - локальный core stack
- **compose.local.diffusers.yml** - локальный override, который включает ML runtime
- **compose.prod.yml** - production-oriented core stack
- **compose.prod.diffusers.yml** - production override для локального Diffusers runtime

### 🔧 Сервисы
- API (`api`)
- Generation Worker (`generation_worker`)
- PostgreSQL
- Redis
- Nginx

## Разделы документации

| Тема | Статус |
|------|--------|
| Getting Started page | 🚧 Coming soon |
| Compose deep-dive pages | 🚧 Coming soon |
| Dockerfile deep-dive | 🚧 Coming soon |
| Nginx deep-dive | 🚧 Coming soon |
| Redis deep-dive | 🚧 Coming soon |
| PostgreSQL deep-dive | 🚧 Coming soon |
| Volumes / networking deep-dive | 🚧 Coming soon |
| [Troubleshooting](../troubleshooting/README.md) | ✅ Доступно |

Пока именно эта README остаётся каноническим Docker overview.

## Быстрый старт

### Local Core Stack
```bash
docker compose --env-file docker/.env.docker -f docker/compose.local.yml up -d --build
```

### Local Diffusers Stack
```bash
docker compose --env-file docker/.env.docker -f docker/compose.local.yml -f docker/compose.local.diffusers.yml up -d --build
```

### Production Core Stack
```bash
docker compose --env-file docker/.env.prod -f docker/compose.prod.yml up -d --build
```

### Production Diffusers Stack
```bash
docker compose --env-file docker/.env.prod -f docker/compose.prod.yml -f docker/compose.prod.diffusers.yml up -d --build
```

## Worker Service

Сервис `generation_worker` обрабатывает generation tasks отдельно от API:

- забирает задачи из очереди
- выполняет генерацию через выбранный provider
- сохраняет артефакты и обновляет lifecycle state

Подробности в [Queue and Workers](../backend/queue-and-workers.md).

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker нужен только если вам нужен локальный GPU Diffusers runtime
- достаточно RAM/disk под выбранный runtime и модели

## Важные заметки

- Собирайте `frontend/dist` до того, как рассчитывать на bundled static frontend delivery.
- Используйте `docker/.env.docker.example` и verify env-файлы как шаблоны, а не как доказательство того, что каждая переменная является app setting.
- Публичный `/metrics` endpoint по умолчанию в app не подключён.
