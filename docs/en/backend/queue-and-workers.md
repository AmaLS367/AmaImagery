# Queue and Workers

## Overview

The application uses an asynchronous task queue model for image generation, allowing HTTP requests to return immediately while heavy processing happens in background workers.

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│  API Layer  │─────▶│  TaskQueue   │
│  (FastAPI)  │      │   (Redis)    │
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Worker     │
                    │  (Background)│
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Provider   │
                    │  (Diffusers) │
                    └──────────────┘
```

## Task Lifecycle

1. **Request** - Client sends generation request to `POST /api/v1/images/generate`
2. **Enqueue** - API validates request and enqueues task, returns `task_id`
3. **Processing** - Worker picks up task, processes via provider
4. **Status** - Client polls `GET /api/v1/images/status/{task_id}` for updates
5. **Completion** - Worker updates status to `completed` or `failed`

## Task Queue

### TaskQueue Interface

The `TaskQueue` protocol provides a unified interface for task management:

- `enqueue(generation_id)` - Adds a persisted generation ID to queue
- `dequeue(timeout)` - Removes task from queue (worker use)

Task lifecycle is tracked in PostgreSQL `generations`, not in Redis status hashes.

### Redis Implementation

The `RedisTaskQueue` implementation uses:
- **Redis List** (`tasks:queue`) - Queue of persisted generation IDs

This design enables:
- Concurrent task consumption by multiple workers
- Distributed task processing
- Redis to remain transport-only while PostgreSQL stores lifecycle state

## Task Status

### Status Values

- `queued` - Task is waiting in queue
- `running` - Task is being processed by worker
- `completed` - Task finished successfully
- `failed` - Task failed with error

### Task ID Format

Task IDs are UUIDs (e.g., `550e8400-e29b-41d4-a716-446655440000`).

## Workers

### Generation Worker

The `generation_worker` process:
- Continuously polls the queue for new tasks
- Loads generation state from database
- Processes tasks via provider registry
- Persists provider state, artifact metadata and final lifecycle status in database

### Running Workers

#### Docker Compose

Workers are included in Docker Compose configurations:

```yaml
generation_worker:
  build:
    context: ..
    dockerfile: Dockerfile
  command: ["python", "-m", "app.entrypoints.generation_worker"]
  depends_on: [redis, postgres]
```

#### Manual Start

```bash
python -m app.entrypoints.generation_worker
```

### Worker Configuration

Workers require:
- Redis connection (`REDIS_URL`)
- Database connection (`DATABASE_URL`)
- Access to model files (same as API)
- GPU access (if using GPU providers)

## API Endpoints

### POST /api/v1/images/generate

Submits a generation task to the queue.

**Request:**
```json
{
  "prompt": "a beautiful landscape",
  "width": 768,
  "height": 1152,
  "steps": 28,
  "guidance_scale": 7.5,
  "style": "anime"
}
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

### GET /api/v1/images/status/{task_id}

Retrieves the current status of a task.

**Response (queued/running):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "created_at": 1234567890,
  "started_at": 1234567900
}
```

**Response (completed):**
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

**Response (failed):**
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

**Error (404):**
```json
{
  "detail": "Task not found"
}
```

## Deployment

### Docker Compose

Workers are automatically started with the `generation_worker` service in Docker Compose.

**Production:**
```bash
docker compose -f docker/compose.prod.yml up -d
```

**Local:**
```bash
docker compose -f docker/compose.local.yml up -d
```

### Scaling Workers

To scale workers, increase the number of `generation_worker` service instances:

```bash
docker compose -f docker/compose.prod.yml up -d --scale generation_worker=3
```

### Dependencies

Workers require:
- **Redis** - For task queue and status storage
- **PostgreSQL** - For saving generation metadata
- **Model files** - Same volume mounts as API service
- **GPU** - If using GPU-based providers

## Monitoring

### Worker Logs

Worker logs are available via Docker:

```bash
docker compose -f docker/compose.prod.yml logs -f generation_worker
```

### Task Metrics

Monitor task queue length and processing times:
- Queue length: `LLEN tasks:queue` in Redis
- Task status: Query `task:{id}` hash in Redis
- Worker health: Check worker process logs

## Troubleshooting

### Worker Not Processing Tasks

1. Check Redis connection: `REDIS_URL` must be set
2. Verify worker is running: `docker compose ps`
3. Check worker logs for errors
4. Ensure queue has tasks: `redis-cli LLEN tasks:queue`

### Tasks Stuck in Queue

1. Check worker is running and healthy
2. Verify provider can load models
3. Check database connectivity
4. Review worker logs for errors

### High Queue Length

1. Scale up workers: `--scale generation_worker=N`
2. Optimize generation parameters (reduce steps/size)
3. Add more GPU resources if using GPU providers

