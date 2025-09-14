$ErrorActionPreference='Stop'
./scripts/windows/preflight.ps1 -Profile prod
./scripts/windows/build_frontend.ps1
docker compose -f docker/compose.prod.yml --env-file docker/.env.prod up -d --build

# подняли контейнеры
docker compose -f docker/compose.prod.yml up -d postgres redis api nginx

# ждём готовность Postgres внутри контейнера
Write-Host "[migrate] waiting for postgres..."
docker compose -f docker/compose.prod.yml exec -T postgres bash -lc 'until pg_isready -h localhost -p 5432; do sleep 1; done'

# применяем alembic-миграции в контейнере api
Write-Host "[migrate] alembic upgrade head"
docker compose -f docker/compose.prod.yml exec -T api bash -lc "alembic -c /app/alembic.ini upgrade head"
if ($LASTEXITCODE -ne 0) { throw "alembic upgrade failed" }

Write-Host "[run_prod] nginx :80 → api :8000"
