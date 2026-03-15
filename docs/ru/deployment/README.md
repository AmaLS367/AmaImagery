# Документация развертывания

## Обзор

Руководство по развертыванию **AmaImagery** в окружениях, которые соответствуют текущему репозиторию.

## Варианты развертывания

### 🐳 Docker развертывание (рекомендуется)
- текущий основной deployment path
- соответствует compose-файлам из репозитория
- самый простой способ держать API, worker, database, Redis и nginx в согласованном состоянии

### ☁️ Cloud / Managed Infrastructure
- возможно, но не оформлено в репозитории как turnkey-guide
- ответственность оператора за перенос Docker/runtime контракта

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

Пока именно эта README остаётся каноническим deployment overview.

## Текущий production checklist

1. ✅ Подготовить реальный production env file
2. ✅ Задать сильный `SECRET_KEY`
3. ✅ Использовать PostgreSQL
4. ✅ Настроить Redis, если включён Redis-backed queueing
5. ✅ Собрать `frontend/dist`
6. ✅ Поднять API и `generation_worker`
7. ✅ Проверить `/api/v1/health` и `/api/v1/healthz`
8. ✅ Запустить smoke generation и убедиться, что history/status согласованы

## Минимальные требования

- достаточно CPU/RAM под API + worker + database + provider runtime
- Docker / Docker Compose, если вы идёте по документированному deployment path
- GPU нужен только если ваш выбранный provider/runtime реально требует локальное GPU execution
- место на диске под outputs, logs и опциональные локальные model assets

## Важные заметки

- Репозиторий сейчас не документирует публичный `/metrics` endpoint как live по умолчанию.
- Worker не является опциональным, если вам нужен документированный async generation lifecycle.
- Переключение между `comfyui` и `diffusers` делается через env/config и compose overrides.
