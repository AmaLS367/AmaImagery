# Provider Verification And Rollout

## Verification Profiles

Use the Docker env templates under `docker/`:

- `docker/.env.verify.diffusers.example` for the `diffusers` verification profile
- `docker/.env.verify.comfyui.example` for the `comfyui` verification profile

Both profiles keep `PROVIDERS_ENABLED=diffusers,comfyui`. The only rollout switch is `PROVIDERS_DEFAULT_NAME`.

## Live Verification Flow

Run the same smoke flow in both profiles:

1. `GET /api/v1/healthz`
2. Register and login a smoke user
3. `POST /api/v1/images/generate`
4. Poll `GET /api/v1/images/status/{task_id}` until `completed` or `failed`
5. Download the signed artifact from `image_url`
6. Verify `GET /api/v1/users/me/generations` contains the same `task_id`, `status`, and `provider_name`

Example:

```bash
cp docker/.env.verify.diffusers.example docker/.env.docker
docker compose -f docker/compose.local.yml up -d --build
SMOKE_EXPECT_PROVIDER=diffusers ./scripts/linux/smoketest.sh http://localhost:8000
```

```bash
cp docker/.env.verify.comfyui.example docker/.env.docker
docker compose -f docker/compose.local.yml up -d --build
SMOKE_EXPECT_PROVIDER=comfyui ./scripts/linux/smoketest.sh http://localhost:8000
```

## Acceptance Criteria

- `status` reaches a terminal DB-backed state: `completed` or `failed`
- terminal `provider_name` matches the verification profile
- `image_url` downloads successfully for completed generations
- history returns the same lifecycle record as the status endpoint
- `comfyui` verification succeeds with websocket or polling fallback

## Rollout Policy

- Canonical default provider after verification: `comfyui`
- Fallback provider: `diffusers`
- Keep both providers enabled during rollout
- Roll back to `PROVIDERS_DEFAULT_NAME=diffusers` if repeated live failures appear in the `submit`, `wait_for_result`, or artifact download path
