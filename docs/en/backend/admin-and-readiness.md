# Admin And Readiness

## Admin Panel

The backend exposes a server-rendered admin surface at `/admin/`.

- Authentication is required.
- Superuser role is required.
- Unauthenticated requests return `401`.
- Authenticated non-superusers return `403`.
- Root `/` redirects authenticated superusers to `/admin/`.

The admin surface currently includes:

- `/admin/generations`
- `/admin/generations/{generation_id}`
- `/admin/users`

The generations list supports query filters:

- `status`
- `provider`

Each generation view shows the persisted lifecycle record from the `generations`
table, including provider name, provider job id, timestamps, error, and artifact
link when the generation is actually artifact-ready.

## Health Endpoints

Two health endpoints are exposed:

### `GET /api/v1/health`

Use this as the lightweight liveness check.

It reports:

- app/process liveness
- provider boot snapshot
- infrastructure summary

Provider boot data includes:

- `enabled_providers`
- `booted_providers`
- `failed_providers`
- `boot_error_summaries`
- `default_provider`
- `default_provider_booted`

This endpoint can still return `200` when a provider failed to boot, because the
application may still be alive.

### `GET /api/v1/healthz`

Use this as the readiness check for generation traffic.

It reports:

- provider readiness
- `default_provider_usable`
- `task_queue_ready`
- `generation_ready`
- infrastructure summary

It returns:

- `200` when the default provider is usable and the task queue path is ready
- `503` when generation traffic should not be sent yet

## Generation Lifecycle Contract

User-visible generation states are normalized to:

- `queued`
- `running`
- `completed`
- `failed`
- `canceled`

Terminal states are:

- `completed`
- `failed`
- `canceled`

Artifact fields are only exposed for `completed` generations with a persisted
artifact path. A failed generation with a missing artifact remains `failed`; it
must not be presented as completed-without-file.
