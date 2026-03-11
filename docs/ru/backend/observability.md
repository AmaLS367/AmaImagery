# Наблюдаемость и управление

## Обзор

Бэкенд предоставляет комплексную наблюдаемость через структурированную обработку ошибок, метрики, feature flags и доменные события. Это обеспечивает мониторинг, отладку и управление конфигурацией в runtime.

## Обработка ошибок

### Иерархия исключений

Все доменные ошибки наследуются от `DomainException`:

```
DomainException (базовый)
├── ValidationException (400)
├── AuthenticationException (401)
├── ResourceNotFoundException (404)
├── TaskNotFoundException (404)
├── ConflictException (409)
├── RateLimitExceededException (429)
├── GenerationFailedException (503)
└── ProviderUnavailableException (503)
```

### Формат ответа об ошибке

Все ошибки API следуют единому формату:

```json
{
  "error": {
    "code": "error_code",
    "message": "Человекочитаемое сообщение об ошибке",
    "details": {
      "field": "дополнительная_информация",
      "resource_id": "123"
    }
  },
  "request_id": "uuid-here"
}
```

### Маппинг исключений

Доменные исключения автоматически маппятся в HTTP статус-коды:

- `ValidationException` → 400 Bad Request
- `AuthenticationException` → 401 Unauthorized
- `ResourceNotFoundException`, `TaskNotFoundException` → 404 Not Found
- `ConflictException` → 409 Conflict
- `RateLimitExceededException` → 429 Too Many Requests
- `GenerationFailedException`, `ProviderUnavailableException` → 503 Service Unavailable
- Неизвестные исключения → 500 Internal Server Error

### Пример использования

```python
from app.core.exceptions import ValidationException, GenerationFailedException

# В use case или сервисе
if invalid_condition:
    raise ValidationException("Неверный ввод", field="prompt")

# В провайдере
if generation_fails:
    raise GenerationFailedException("Генерация превысила таймаут", details={"timeout": 300})
```

## Метрики

### Prometheus метрики

Бэкенд экспортирует метрики Prometheus на эндпоинте `/metrics`.

### Метрики провайдеров

**`provider_generation_total`** - Счетчик
- Метки: `provider_name`, `status` (started/success/error)
- Отслеживает общее количество запросов генерации на провайдер

**`provider_generation_duration_seconds`** - Гистограмма
- Метки: `provider_name`
- Ведра: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
- Измеряет время генерации

**`provider_generation_errors_total`** - Счетчик
- Метки: `provider_name`, `error_type`
- Отслеживает ошибки генерации по типу

### Метрики очереди

**`queue_size`** - Gauge
- Метки: `queue_name`
- Текущее количество задач в очереди

**`queue_enqueued_total`** - Счетчик
- Метки: `queue_name`
- Всего задач поставлено в очередь

**`queue_dequeued_total`** - Счетчик
- Метки: `queue_name`
- Всего задач взято из очереди

### Метрики воркеров

**`worker_task_duration_seconds`** - Гистограмма
- Метки: `queue_name`, `task_type`
- Ведра: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
- Время обработки задач

**`worker_task_status_total`** - Счетчик
- Метки: `queue_name`, `task_type`, `status` (started/success/error)
- Количество задач по статусам

**`worker_task_errors_total`** - Счетчик
- Метки: `queue_name`, `task_type`, `error_type`
- Количество ошибок задач

### Чтение метрик

Запросы к Prometheus:

```promql
# Процент успешных генераций
rate(provider_generation_total{status="success"}[5m]) / 
rate(provider_generation_total{status="started"}[5m])

# Среднее время генерации
rate(provider_generation_duration_seconds_sum[5m]) / 
rate(provider_generation_duration_seconds_count[5m])

# Размер очереди
queue_size{queue_name="generation"}

# Пропускная способность воркеров
rate(worker_task_status_total{status="success"}[5m])
```

## Feature Flags

### Конфигурация

Feature flags настраиваются через переменную окружения `FEATURE_FLAGS`:

```bash
# JSON формат
FEATURE_FLAGS='{"image_generation": true, "ip_adapter": false}'

# Простой формат
FEATURE_FLAGS='image_generation=true,ip_adapter=false'

# Формат списка (все включены)
FEATURE_FLAGS='image_generation,image_editing'
```

### Дефолтные флаги

- `image_generation` - Включить генерацию изображений (по умолчанию: `true`)
- `image_editing` - Включить редактирование изображений (по умолчанию: `true`)
- `image_upscaling` - Включить апскейл изображений (по умолчанию: `true`)
- `ip_adapter` - Включить функции IP-Adapter (по умолчанию: `true`)
- `batch_generation` - Включить пакетную генерацию (по умолчанию: `true`)

### Использование

```python
from app.core.feature_flags import get_feature_flag_service

feature_flags = get_feature_flag_service()

if feature_flags.is_enabled("image_generation"):
    # Фича включена
    pass

if feature_flags.is_disabled("ip_adapter"):
    # Фича выключена
    pass
```

### Включение/выключение фич

**Через переменную окружения:**

```bash
# Выключить генерацию изображений
export FEATURE_FLAGS='{"image_generation": false}'

# Включить только генерацию
export FEATURE_FLAGS='image_generation=true,image_editing=false,image_upscaling=false'
```

**Поведение в runtime:**

- Отключенные фичи возвращают 503 Service Unavailable
- Реестр провайдеров проверяет флаги перед регистрацией
- API эндпоинты валидируют флаги перед обработкой

## Доменные события

### Типы событий

**`ImageGeneratedEvent`**
- Публикуется при успешной генерации изображения
- Payload: `task_id`, `user_id`, `image_path`, `metadata`

**`GenerationFailedEvent`**
- Публикуется при ошибке генерации изображения
- Payload: `task_id`, `user_id`, `error`, `error_type`

### Структура события

Все события наследуются от `DomainEvent`:

```python
@dataclass
class DomainEvent:
    name: str
    occurred_at: datetime
    payload: Dict[str, Any]
```

### Подписка на события

```python
from app.core.events import get_event_bus, ImageGeneratedEvent

event_bus = get_event_bus()

# Синхронный обработчик
def handle_generation(event: ImageGeneratedEvent):
    print(f"Изображение сгенерировано: {event.payload['image_path']}")

# Асинхронный обработчик
async def handle_generation_async(event: ImageGeneratedEvent):
    await send_notification(event.payload['user_id'])

# Подписка
event_bus.subscribe("image_generated", handle_generation)
event_bus.subscribe("image_generated", handle_generation_async)
```

### Публикация событий

События автоматически публикуются:
- **Воркерами** - После успешной/неуспешной генерации
- **Use Cases** - Могут публиковать события для бизнес-операций

```python
from app.core.events import get_event_bus, ImageGeneratedEvent

event_bus = get_event_bus()
await event_bus.publish(
    ImageGeneratedEvent(
        task_id="123",
        user_id="user-456",
        image_path="/outputs/image.png",
        metadata={"width": 768, "height": 1152}
    )
)
```

### Лучшие практики обработчиков событий

1. **Держать обработчики легкими** - Не блокировать публикацию событий
2. **Обрабатывать ошибки корректно** - Исключения в обработчиках не прерывают публикацию
3. **Использовать async обработчики** - Для I/O операций (БД, HTTP)
4. **Идемпотентные операции** - Обработчики должны быть безопасны для повторов

## Интеграция

### Обработка ошибок в API

Глобальные обработчики ошибок автоматически:
- Маппят доменные исключения в HTTP статус-коды
- Форматируют ответы об ошибках единообразно
- Включают request ID для трассировки
- Логируют ошибки с контекстом

### Сбор метрик

Метрики автоматически собираются:
- Операции провайдеров отслеживают метрики генерации
- Операции очереди отслеживают метрики очереди
- Операции воркеров отслеживают метрики задач

### Проверка Feature Flags

Feature flags проверяются:
- При инициализации реестра провайдеров
- В обработчиках API эндпоинтов
- Могут проверяться в любом сервисе/use case

### Публикация событий

События публикуются:
- В воркере после завершения/ошибки задачи
- Могут публиковаться из use cases
- Обработчики выполняются асинхронно

## Настройка мониторинга

### Конфигурация Prometheus

```yaml
scrape_configs:
  - job_name: 'amaimagery-backend'
    scrape_interval: 15s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana дашборды

Ключевые метрики для мониторинга:
- Процент успешных генераций
- Среднее время генерации
- Размер очереди
- Пропускная способность воркеров
- Частота ошибок по типам

### Правила алертинга

Пример алертов Prometheus:

```yaml
groups:
  - name: amaimagery_alerts
    rules:
      - alert: HighGenerationErrorRate
        expr: rate(provider_generation_errors_total[5m]) > 0.1
        for: 5m
        
      - alert: LargeQueueBacklog
        expr: queue_size{queue_name="generation"} > 100
        for: 10m
        
      - alert: SlowGeneration
        expr: histogram_quantile(0.95, provider_generation_duration_seconds) > 60
        for: 5m
```

