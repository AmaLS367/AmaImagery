# Наблюдаемость и управление

## Обзор

Бэкенд даёт наблюдаемость через структурированное логирование, доменные исключения, feature flags, доменные события, readiness checks и metrics modules внутри кодовой базы.

## Что реально есть сейчас

### 🧾 Обработка ошибок
- доменные исключения и их HTTP mapping
- request-scoped logging и error context
- явная фиксация generation/provider failures

### 📊 Metrics Modules
- queue metrics modules есть в `app/metrics/queue.py`
- provider metrics modules есть в `app/metrics/providers.py`
- exporter-related code есть в `app/metrics/`

### 🚦 Health и Readiness
- `GET /api/v1/health` для liveness
- `GET /api/v1/healthz` для generation readiness
- admin pages для просмотра persisted runtime state

### 🎛️ Feature Flags
Настраиваются через `FEATURE_FLAGS`.

Текущие ключи по умолчанию в конфиге:
- `image_generation`
- `image_editing`
- `image_upscaling`
- `ip_adapter`
- `batch_generation`

Важно:
- часть флагов существует раньше, чем появляется полностью публичная feature
- сам факт наличия флага не означает, что уже есть стабильный public API

### 📣 Доменные события
В event bus сейчас есть:
- `ImageGeneratedEvent`
- `GenerationFailedEvent`

## Публичные метрики: важная оговорка

В репозитории есть Prometheus-oriented metrics code, но FastAPI app сейчас **не** монтирует публичный `/metrics` endpoint по умолчанию.

То есть:

- код для metrics integration существует
- внутренняя или кастомная exporter wiring возможна
- готовый публичный `/metrics` route нельзя документировать как уже live, пока вы не подключили его сами

## Пример конфигурации Feature Flags

```bash
FEATURE_FLAGS='{"image_generation": true, "ip_adapter": false}'
FEATURE_FLAGS='image_generation=true,ip_adapter=false'
```

## Пример работы с событиями

```python
from app.core.events import get_event_bus, ImageGeneratedEvent

event_bus = get_event_bus()

await event_bus.publish(
    ImageGeneratedEvent(
        task_id="123",
        user_id="user-456",
        image_path="/outputs/image.png",
        metadata={"width": 768, "height": 1152},
    )
)
```

## Planned / Integration-Specific Areas

- Публичный Prometheus scrape endpoint — Coming soon / integration-specific
- Grafana dashboard guides — Coming soon
- Alerting playbooks — Coming soon
