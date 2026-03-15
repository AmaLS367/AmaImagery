# Очередь и воркеры

## Обзор

Приложение использует асинхронную модель очереди задач для генерации изображений, позволяя HTTP-запросам возвращаться немедленно, в то время как тяжелая обработка происходит в фоновых воркерах.

## Архитектура

```
┌─────────────┐
│   Клиент    │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│  API слой    │─────▶│  TaskQueue   │
│  (FastAPI)   │      │   (Redis)    │
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Воркер     │
                    │  (Фоновый)   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Провайдер  │
                    │  (Diffusers) │
                    └──────────────┘
```

## Жизненный цикл задачи

1. **Запрос** - Клиент отправляет запрос на генерацию в `POST /api/v1/images/generate`
2. **Постановка в очередь** - API валидирует запрос и ставит задачу в очередь, возвращает `task_id`
3. **Обработка** - Воркер берет задачу, обрабатывает через провайдер
4. **Статус** - Клиент опрашивает `GET /api/v1/images/status/{task_id}` для обновлений
5. **Завершение** - Воркер обновляет статус на `completed` или `failed`

## Очередь задач

### Интерфейс TaskQueue

Протокол `TaskQueue` предоставляет единый интерфейс для управления задачами:

- `enqueue(generation_id)` - Добавляет в очередь идентификатор уже сохраненной генерации
- `dequeue(timeout)` - Удаляет задачу из очереди (используется воркером)

Жизненный цикл задачи отслеживается в PostgreSQL `generations`, а не в Redis status hash.

### Реализация Redis

Реализация `RedisTaskQueue` использует:
- **Redis List** (`tasks:queue`) - Очередь идентификаторов задач

Этот дизайн обеспечивает:
- Параллельную обработку задач несколькими воркерами
- Распределенную обработку задач
- Использование Redis только как транспортной очереди, пока authoritative lifecycle живет в PostgreSQL

## Статус задачи

### Значения статуса

- `queued` - Задача ожидает в очереди
- `running` - Задача обрабатывается воркером
- `completed` - Задача успешно завершена
- `failed` - Задача завершилась с ошибкой

### Формат Task ID

Идентификаторы задач - это UUID (например, `550e8400-e29b-41d4-a716-446655440000`).

## Воркеры

### Воркер генерации

Процесс `generation_worker`:
- Постоянно опрашивает очередь на наличие новых задач
- Загружает состояние генерации из базы данных
- Обрабатывает задачи через реестр провайдеров
- Сохраняет состояние провайдера, метаданные артефакта и финальный lifecycle в базу данных

### Запуск воркеров

#### Docker Compose

Воркеры включены в конфигурации Docker Compose:

```yaml
generation_worker:
  build:
    context: ..
    dockerfile: Dockerfile
    target: runtime-core
  command: ["python", "-m", "app.entrypoints.generation_worker"]
  depends_on: [redis, postgres]
```

#### Ручной запуск

```bash
python -m app.entrypoints.generation_worker
```

### Конфигурация воркера

Воркеры требуют:
- Подключение к Redis (`REDIS_URL`)
- Подключение к базе данных (`DATABASE_URL`)
- Доступ к runtime выбранного провайдера
- Доступ к GPU только при использовании `runtime-ml` / режима Diffusers

## API эндпоинты

### POST /api/v1/images/generate

Отправляет задачу генерации в очередь.

**Запрос:**
```json
{
  "prompt": "красивый пейзаж",
  "width": 768,
  "height": 1152,
  "steps": 28,
  "guidance_scale": 7.5,
  "style": "anime"
}
```

**Ответ:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

### GET /api/v1/images/status/{task_id}

Получает текущий статус задачи.

**Ответ (queued/running):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "created_at": 1234567890,
  "started_at": 1234567900
}
```

**Ответ (completed):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "image_path": "/app/outputs/image.png",
  "image_filename": "image.png",
  "metadata": {
    "width": 768,
    "height": 1152,
    "steps": 28,
    "model_id": "model-name"
  },
  "created_at": 1234567890,
  "started_at": 1234567900,
  "completed_at": 1234568000
}
```

**Ответ (failed):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error": "Generation timed out",
  "created_at": 1234567890,
  "started_at": 1234567900,
  "completed_at": 1234568000
}
```

**Ошибка (404):**
```json
{
  "detail": "Task not found"
}
```

## Деплой

### Docker Compose

Воркеры автоматически запускаются с сервисом `generation_worker` в Docker Compose.

**Продакшн:**
```bash
docker compose -f docker/compose.prod.yml up -d
```

**Продакшн с локальным Diffusers runtime:**
```bash
docker compose -f docker/compose.prod.yml -f docker/compose.prod.diffusers.yml up -d
```

**Локально:**
```bash
docker compose -f docker/compose.local.yml up -d
```

**Локально с Diffusers runtime:**
```bash
docker compose -f docker/compose.local.yml -f docker/compose.local.diffusers.yml up -d
```

### Масштабирование воркеров

Для масштабирования воркеров увеличьте количество экземпляров сервиса `generation_worker`:

```bash
docker compose -f docker/compose.prod.yml up -d --scale generation_worker=3
```

### Зависимости

Воркеры требуют:
- **Redis** - Для очереди задач и хранения статусов
- **PostgreSQL** - Для сохранения метаданных генерации
- **Доступность ComfyUI** - Для `runtime-core` / ComfyUI-only деплоя
- **Файлы моделей и GPU** - Только для `runtime-ml` / режима Diffusers

## Мониторинг

### Логи воркера

Логи воркера доступны через Docker:

```bash
docker compose -f docker/compose.prod.yml logs -f generation_worker
```

### Метрики задач

Мониторинг длины очереди и времени обработки:
- Длина очереди: `LLEN tasks:queue` в Redis
- Статус задачи: Запрос hash `task:{id}` в Redis
- Здоровье воркера: Проверка логов процесса воркера

## Устранение неполадок

### Воркер не обрабатывает задачи

1. Проверьте подключение к Redis: `REDIS_URL` должен быть установлен
2. Убедитесь, что воркер запущен: `docker compose ps`
3. Проверьте логи воркера на ошибки
4. Убедитесь, что в очереди есть задачи: `redis-cli LLEN tasks:queue`

### Задачи застряли в очереди

1. Проверьте, что воркер запущен и здоров
2. Убедитесь, что провайдер может загрузить модели
3. Проверьте подключение к базе данных
4. Просмотрите логи воркера на ошибки

### Высокая длина очереди

1. Масштабируйте воркеры: `--scale generation_worker=N`
2. Оптимизируйте параметры генерации (уменьшите steps/size)
3. Добавьте больше GPU ресурсов, если используются GPU-провайдеры

