# Observability and Management

## Overview

The backend exposes observability through structured logging, domain exceptions, feature flags, domain events, readiness checks, and metrics modules in the codebase.

## What Exists Today

### 🧾 Error Handling
- domain exceptions and HTTP mapping
- request-scoped logging and error context
- explicit generation/provider failure reporting

### 📊 Metrics Modules
- queue metrics modules exist in `app/metrics/queue.py`
- provider metrics modules exist in `app/metrics/providers.py`
- exporter-related code exists in `app/metrics/`

### 🚦 Health and Readiness
- `GET /api/v1/health` for liveness
- `GET /api/v1/healthz` for generation readiness
- admin pages for inspecting persisted runtime state

### 🎛️ Feature Flags
Configured through `FEATURE_FLAGS`.

Current default keys in config:
- `image_generation`
- `image_editing`
- `image_upscaling`
- `ip_adapter`
- `batch_generation`

Important note:
- some flags exist ahead of fully public features
- the presence of a flag does not automatically mean a stable public API already exists

### 📣 Domain Events
The event bus currently includes:
- `ImageGeneratedEvent`
- `GenerationFailedEvent`

## Public Metrics Note

The repository contains Prometheus-oriented metrics code, but the FastAPI app does **not** mount a public `/metrics` endpoint by default right now.

So:

- metrics integration code exists
- internal or custom exporter wiring is possible
- a ready-to-scrape public `/metrics` route should not be documented as live unless you wire it in yourself

## Example Feature Flag Configuration

```bash
FEATURE_FLAGS='{"image_generation": true, "ip_adapter": false}'
FEATURE_FLAGS='image_generation=true,ip_adapter=false'
```

## Example Event Usage

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

- Public Prometheus scrape endpoint — Coming soon / integration-specific
- Grafana dashboard guides — Coming soon
- Alerting playbooks — Coming soon
