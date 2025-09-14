# Skrypty wdrożeniowe — Użycie

## Wymagania wstępne
- Docker + Docker Compose
- Node.js (npm lub pnpm) — budowa frontendu
- Sterowniki NVIDIA + `nvidia-smi` (tylko profil GPU)

## Struktura
- `docker/compose.local.yml` — stos deweloperski (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — środowisko zbliżone do produkcji (rezerwacja GPU)
- `docker/compose.cpu.yml` — fallback CPU
- `docker/.env.*.example` — szablony środowisk
- `docker/nginx.conf` — statyki + proxy na API
- `scripts/linux/*` — skrypty Bash (Linux)
- `scripts/macos/*` — skrypty Bash (macOS)
- `scripts/windows/*` — skrypty PowerShell (Windows)

## Typowy przebieg (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (po dodaniu Alembic)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Typowy przebieg (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (po dodaniu Alembic)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Uruchomienie zbliżone do produkcji
- Wypełnij `docker/.env.prod` na podstawie `.env.prod.example`
- Zbuduj FE: `build_frontend` (linux/windows)
- Start: `run_prod` (linux/windows)
- Smoke test: `smoketest` na publicznym URL lub `http://host:80`

## Uwagi
- Frontend **musi** być serwowany z `frontend/dist` (kopiowany do `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` są wymagane.
- GPU: `compose.prod.yml`; fallback CPU: `compose.cpu.yml`.
