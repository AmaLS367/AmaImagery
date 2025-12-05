# Observability and Management

## Overview

The backend provides comprehensive observability through structured error handling, metrics, feature flags, and domain events. This enables monitoring, debugging, and runtime configuration management.

## Error Handling

### Exception Hierarchy

All domain errors inherit from `DomainException`:

```
DomainException (base)
├── ValidationException (400)
├── AuthenticationException (401)
├── ResourceNotFoundException (404)
├── TaskNotFoundException (404)
├── ConflictException (409)
├── RateLimitExceededException (429)
├── GenerationFailedException (503)
└── ProviderUnavailableException (503)
```

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      "field": "additional_info",
      "resource_id": "123"
    }
  },
  "request_id": "uuid-here"
}
```

### Exception Mapping

Domain exceptions are automatically mapped to HTTP status codes:

- `ValidationException` → 400 Bad Request
- `AuthenticationException` → 401 Unauthorized
- `ResourceNotFoundException`, `TaskNotFoundException` → 404 Not Found
- `ConflictException` → 409 Conflict
- `RateLimitExceededException` → 429 Too Many Requests
- `GenerationFailedException`, `ProviderUnavailableException` → 503 Service Unavailable
- Unknown exceptions → 500 Internal Server Error

### Usage Example

```python
from app.core.exceptions import ValidationException, GenerationFailedException

# In use case or service
if invalid_condition:
    raise ValidationException("Invalid input", field="prompt")

# In provider
if generation_fails:
    raise GenerationFailedException("Generation timed out", details={"timeout": 300})
```

## Metrics

### Prometheus Metrics

The backend exports Prometheus metrics at `/metrics` endpoint.

### Provider Metrics

**`provider_generation_total`** - Counter
- Labels: `provider_name`, `status` (started/success/error)
- Tracks total generation requests per provider

**`provider_generation_duration_seconds`** - Histogram
- Labels: `provider_name`
- Buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
- Measures generation time

**`provider_generation_errors_total`** - Counter
- Labels: `provider_name`, `error_type`
- Tracks generation errors by type

### Queue Metrics

**`queue_size`** - Gauge
- Labels: `queue_name`
- Current number of tasks in queue

**`queue_enqueued_total`** - Counter
- Labels: `queue_name`
- Total tasks enqueued

**`queue_dequeued_total`** - Counter
- Labels: `queue_name`
- Total tasks dequeued

### Worker Metrics

**`worker_task_duration_seconds`** - Histogram
- Labels: `queue_name`, `task_type`
- Buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
- Task processing time

**`worker_task_status_total`** - Counter
- Labels: `queue_name`, `task_type`, `status` (started/success/error)
- Task status counts

**`worker_task_errors_total`** - Counter
- Labels: `queue_name`, `task_type`, `error_type`
- Task error counts

### Reading Metrics

Query Prometheus for metrics:

```promql
# Generation success rate
rate(provider_generation_total{status="success"}[5m]) / 
rate(provider_generation_total{status="started"}[5m])

# Average generation time
rate(provider_generation_duration_seconds_sum[5m]) / 
rate(provider_generation_duration_seconds_count[5m])

# Queue backlog
queue_size{queue_name="generation"}

# Worker throughput
rate(worker_task_status_total{status="success"}[5m])
```

## Feature Flags

### Configuration

Feature flags are configured via `FEATURE_FLAGS` environment variable:

```bash
# JSON format
FEATURE_FLAGS='{"image_generation": true, "ip_adapter": false}'

# Simple format
FEATURE_FLAGS='image_generation=true,ip_adapter=false'

# List format (all enabled)
FEATURE_FLAGS='image_generation,image_editing'
```

### Default Flags

- `image_generation` - Enable image generation (default: `true`)
- `image_editing` - Enable image editing (default: `true`)
- `image_upscaling` - Enable image upscaling (default: `true`)
- `ip_adapter` - Enable IP-Adapter features (default: `true`)
- `batch_generation` - Enable batch generation (default: `true`)

### Usage

```python
from app.core.feature_flags import get_feature_flag_service

feature_flags = get_feature_flag_service()

if feature_flags.is_enabled("image_generation"):
    # Feature is enabled
    pass

if feature_flags.is_disabled("ip_adapter"):
    # Feature is disabled
    pass
```

### Enabling/Disabling Features

**Via Environment Variable:**

```bash
# Disable image generation
export FEATURE_FLAGS='{"image_generation": false}'

# Enable only generation
export FEATURE_FLAGS='image_generation=true,image_editing=false,image_upscaling=false'
```

**Runtime Behavior:**

- Disabled features return 503 Service Unavailable
- Provider registry checks flags before registration
- API endpoints validate flags before processing

## Domain Events

### Event Types

**`ImageGeneratedEvent`**
- Published when image generation succeeds
- Payload: `task_id`, `user_id`, `image_path`, `metadata`

**`GenerationFailedEvent`**
- Published when image generation fails
- Payload: `task_id`, `user_id`, `error`, `error_type`

### Event Structure

All events inherit from `DomainEvent`:

```python
@dataclass
class DomainEvent:
    name: str
    occurred_at: datetime
    payload: Dict[str, Any]
```

### Subscribing to Events

```python
from app.core.events import get_event_bus, ImageGeneratedEvent

event_bus = get_event_bus()

# Sync handler
def handle_generation(event: ImageGeneratedEvent):
    print(f"Image generated: {event.payload['image_path']}")

# Async handler
async def handle_generation_async(event: ImageGeneratedEvent):
    await send_notification(event.payload['user_id'])

# Subscribe
event_bus.subscribe("image_generated", handle_generation)
event_bus.subscribe("image_generated", handle_generation_async)
```

### Publishing Events

Events are automatically published by:
- **Workers** - After successful/failed generation
- **Use Cases** - Can publish events for business operations

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

### Event Handler Best Practices

1. **Keep handlers lightweight** - Don't block event publishing
2. **Handle errors gracefully** - Exceptions in handlers don't fail event publishing
3. **Use async handlers** - For I/O operations (database, HTTP)
4. **Idempotent operations** - Handlers should be safe to retry

## Integration

### Error Handling in API

Global error handlers automatically:
- Map domain exceptions to HTTP status codes
- Format error responses consistently
- Include request IDs for tracing
- Log errors with context

### Metrics Collection

Metrics are automatically collected:
- Provider operations track generation metrics
- Queue operations track queue metrics
- Worker operations track task metrics

### Feature Flag Checks

Feature flags are checked:
- In provider registry initialization
- In API endpoint handlers
- Can be checked in any service/use case

### Event Publishing

Events are published:
- In worker after task completion/failure
- Can be published from use cases
- Handlers execute asynchronously

## Monitoring Setup

### Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'genai-backend'
    scrape_interval: 15s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana Dashboards

Key metrics to monitor:
- Generation success rate
- Average generation time
- Queue backlog size
- Worker throughput
- Error rates by type

### Alerting Rules

Example Prometheus alerts:

```yaml
groups:
  - name: genai_alerts
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

