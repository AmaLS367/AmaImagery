# Верификация И Rollout Провайдеров

## Профили Верификации

Используйте шаблоны env в `docker/`:

- `docker/.env.verify.diffusers.example` для профиля верификации `diffusers`
- `docker/.env.verify.comfyui.example` для профиля верификации `comfyui`

Оба профиля держат `PROVIDERS_ENABLED=diffusers,comfyui`. Единственный rollout-переключатель - `PROVIDERS_DEFAULT_NAME`.

## Live Verification Flow

Один и тот же smoke flow нужно прогнать в обоих профилях:

1. `GET /api/v1/healthz`
2. Регистрация и логин smoke-пользователя
3. `POST /api/v1/images/generate`
4. Polling `GET /api/v1/images/status/{task_id}` до `completed` или `failed`
5. Скачивание signed artifact по `image_url`
6. Проверка, что `GET /api/v1/users/me/generations` содержит тот же `task_id`, `status` и `provider_name`

Пример:

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

## Критерии Приемки

- `status` доходит до terminal DB-backed состояния: `completed` или `failed`
- terminal `provider_name` совпадает с профилем верификации
- `image_url` успешно скачивается для completed generation
- history возвращает ту же lifecycle-запись, что и status endpoint
- верификация `comfyui` проходит и через websocket, и через polling fallback при необходимости

## Rollout Policy

- Канонический default provider после верификации: `comfyui`
- Fallback provider: `diffusers`
- Во время rollout оба провайдера должны оставаться включенными
- Rollback: вернуть `PROVIDERS_DEFAULT_NAME=diffusers`, если в live среде повторяются сбои в `submit`, `wait_for_result` или artifact download path
