# Deployment Scripts — Usage

This package provides cross‑OS scripts to run your app locally and in a prod‑like setup.

## Prereqs
- Docker + Docker Compose
- Node.js (npm or pnpm) to build the frontend
- NVIDIA drivers + `nvidia-smi` (GPU profile only)

## Structure
- `docker/compose.local.yml` — dev stack (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — prod‑like stack (GPU reservation)
- `docker/compose.cpu.yml` — CPU fallback
- `docker/.env.*.example` — environment templates
- `docker/nginx.conf` — static + API proxy
- `scripts/linux/*` — Bash scripts (Linux)
- `scripts/macos/*` — Bash scripts (macOS)
- `scripts/windows/*` — PowerShell scripts (Windows)

## Typical flow (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (once you add Alembic)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Typical flow (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (once you add Alembic)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Prod‑like run
- Fill `docker/.env.prod` based on `.env.prod.example`
- Build FE: `build_frontend` (linux/windows)
- Start: `run_prod` (linux/windows)
- Smoke test: `smoketest` against the public URL or `http://host:80`

## Notes
- Frontend **must** be served from `frontend/dist` (copied into `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` are mandatory.
- GPU: use `compose.prod.yml`; CPU fallback: `compose.cpu.yml`.
