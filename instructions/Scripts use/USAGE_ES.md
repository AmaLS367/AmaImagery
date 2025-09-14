# Scripts de despliegue — Uso

## Requisitos previos
- Docker + Docker Compose
- Node.js (npm o pnpm) para construir el frontend
- Controladores NVIDIA + `nvidia-smi` (solo perfil GPU)

## Estructura
- `docker/compose.local.yml` — stack de desarrollo (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — stack similar a producción (reserva de GPU)
- `docker/compose.cpu.yml` — fallback a CPU
- `docker/.env.*.example` — plantillas de entorno
- `docker/nginx.conf` — estáticos + proxy al API
- `scripts/linux/*` — scripts Bash (Linux)
- `scripts/macos/*` — scripts Bash (macOS)
- `scripts/windows/*` — scripts PowerShell (Windows)

## Flujo típico (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (cuando añadas Alembic)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Flujo típico (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (cuando añadas Alembic)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Ejecución tipo producción
- Completa `docker/.env.prod` a partir de `.env.prod.example`
- Construye el FE: `build_frontend` (linux/windows)
- Arranque: `run_prod` (linux/windows)
- Smoke test: `smoketest` contra la URL pública o `http://host:80`

## Notas
- El frontend **debe** servirse desde `frontend/dist` (copiado a `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` son obligatorias.
- GPU: `compose.prod.yml`; fallback CPU: `compose.cpu.yml`.
