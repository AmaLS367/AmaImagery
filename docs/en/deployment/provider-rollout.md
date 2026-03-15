# Provider Verification And Rollout

## Verification Profiles

Use the Docker env templates under `docker/`:

- `docker/.env.verify.diffusers.example` for the `diffusers` verification profile
- `docker/.env.verify.comfyui.example` for the `comfyui` verification profile

The profiles represent two different runtime modes:

- `comfyui`: `PROVIDERS_ENABLED=comfyui` on the lightweight `runtime-core` image
- `diffusers`: `PROVIDERS_ENABLED=diffusers` on the `runtime-ml` image

## Live Verification Flow

Run the same smoke flow in both profiles:

1. `GET /api/v1/health`
2. `GET /api/v1/healthz`
3. Confirm `generation_ready=true` and `default_provider_usable=true`
2. Register and login a smoke user
3. `POST /api/v1/images/generate`
4. Poll `GET /api/v1/images/status/{task_id}` until `completed` or `failed`
5. Download the signed artifact from `image_url`
6. Verify `GET /api/v1/users/me/generations` contains the same `task_id`, `status`, and `provider_name`

Example:

```bash
cp docker/.env.verify.diffusers.example docker/.env.docker
docker compose -f docker/compose.local.yml -f docker/compose.local.diffusers.yml up -d --build
SMOKE_EXPECT_PROVIDER=diffusers ./scripts/linux/smoketest.sh http://localhost:8000
```

```bash
cp docker/.env.verify.comfyui.example docker/.env.docker
docker compose -f docker/compose.local.yml up -d --build
SMOKE_EXPECT_PROVIDER=comfyui ./scripts/linux/smoketest.sh http://localhost:8000
```

## Acceptance Criteria

- `/api/v1/health` exposes provider boot state for the selected rollout profile
- `/api/v1/healthz` returns `200` only when the default generation provider is usable
- `status` reaches a terminal DB-backed state: `completed` or `failed`
- terminal `provider_name` matches the verification profile
- `image_url` downloads successfully for completed generations
- history returns the same lifecycle record as the status endpoint
- `comfyui` verification succeeds with websocket or polling fallback

## Rollout Policy

- Canonical default provider after verification: `comfyui`
- Fallback provider: `diffusers`
- Keep the default Docker runtime lightweight and ComfyUI-only unless a deployment explicitly needs local Diffusers
- Roll forward to Diffusers by adding `docker/compose.local.diffusers.yml` or `docker/compose.prod.diffusers.yml`
