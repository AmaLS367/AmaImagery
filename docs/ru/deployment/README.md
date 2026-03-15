# Документация развертывания

## Обзор

Руководство по развертыванию **AmaImagery**.

## Варианты развертывания

### 🐳 Docker развертывание (рекомендуется)
- текущий основной deployment path
- соответствует compose-файлам из репозитория
- самый простой способ держать API, worker, database, Redis и nginx в согласованном состоянии

### ☁️ Cloud / Managed Infrastructure
- turnkey-руководство для этого варианта не предоставляется
- операторы самостоятельно адаптируют Docker/runtime контракт под свою инфраструктуру

### 🖥️ Bare Metal
- возможно для продвинутых операторов
- особенно актуально при локальном GPU/Diffusers runtime

## Разделы документации

| Тема | Статус |
|------|--------|
| Requirements page | 🚧 Coming soon |
| Environment deep-dive | 🚧 Coming soon |
| Production checklist page | 🚧 Coming soon |
| TLS / SSL page | 🚧 Coming soon |
| Monitoring page | 🚧 Coming soon |
| Scaling page | 🚧 Coming soon |
| Cloud guides | 🚧 Coming soon |
| Maintenance playbook | 🚧 Coming soon |
| [Provider Rollout](./provider-rollout.md) | ✅ Доступно |

## Production Checklist

1. ✅ Подготовить production env file
2. ✅ Задать сильный `SECRET_KEY`
3. ✅ Использовать PostgreSQL
4. ✅ Настроить Redis, если включён Redis-backed queueing
5. ✅ Собрать `frontend/dist`
6. ✅ Поднять API и `generation_worker`
7. ✅ Проверить `/api/v1/health` и `/api/v1/healthz`
8. ✅ Запустить smoke generation и убедиться, что history/status согласованы

## Минимальные требования

- достаточно CPU/RAM под API + worker + database + provider runtime
- Docker / Docker Compose для Docker-based развёртывания
- GPU нужен только если ваш выбранный provider/runtime реально требует локальное GPU execution
- место на диске под outputs, logs и опциональные локальные model assets

## Важные заметки

- Публичный `/metrics` endpoint по умолчанию не смонтирован.
- Worker обязателен для async generation lifecycle.
- Переключение между `comfyui` и `diffusers` делается через env/config и compose overrides.
