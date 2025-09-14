# Deploymentscripts — Gebruik

## Vereisten
- Docker + Docker Compose
- Node.js (npm of pnpm) om de frontend te bouwen
- NVIDIA‑drivers + `nvidia-smi` (alleen GPU‑profiel)

## Structuur
- `docker/compose.local.yml` — dev‑stack (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — productie‑achtig (GPU‑reservering)
- `docker/compose.cpu.yml` — CPU‑fallback
- `docker/.env.*.example` — omgevingssjablonen
- `docker/nginx.conf` — statisch + API‑proxy
- `scripts/linux/*` — Bash‑scripts (Linux)
- `scripts/macos/*` — Bash‑scripts (macOS)
- `scripts/windows/*` — PowerShell‑scripts (Windows)

## Typische flow (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (wanneer je Alembic toevoegt)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Typische flow (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (wanneer je Alembic toevoegt)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Prod‑achtige run
- Vul `docker/.env.prod` in op basis van `.env.prod.example`
- Bouw FE: `build_frontend` (linux/windows)
- Start: `run_prod` (linux/windows)
- Smoke test: `smoketest` tegen de publieke URL of `http://host:80`

## Opmerkingen
- Frontend **moet** uit `frontend/dist` geserveerd worden (gekopieerd naar `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` zijn verplicht.
- GPU: `compose.prod.yml`; CPU‑fallback: `compose.cpu.yml`.
