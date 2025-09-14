# Deployment‑Skripte — Verwendung

## Voraussetzungen
- Docker + Docker Compose
- Node.js (npm oder pnpm) zum Bauen des Frontends
- NVIDIA‑Treiber + `nvidia-smi` (nur GPU‑Profil)

## Struktur
- `docker/compose.local.yml` — Dev‑Stack (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — produktionsnaher Stack (GPU‑Reservierung)
- `docker/compose.cpu.yml` — CPU‑Fallback
- `docker/.env.*.example` — Umgebungs‑Templates
- `docker/nginx.conf` — Static + API‑Proxy
- `scripts/linux/*` — Bash‑Skripte (Linux)
- `scripts/macos/*` — Bash‑Skripte (macOS)
- `scripts/windows/*` — PowerShell‑Skripte (Windows)

## Typischer Ablauf (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (sobald Alembic hinzugefügt ist)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Typischer Ablauf (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (sobald Alembic hinzugefügt ist)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Produktionsähnlicher Run
- `docker/.env.prod` anhand von `.env.prod.example` ausfüllen
- Frontend bauen: `build_frontend` (linux/windows)
- Start: `run_prod` (linux/windows)
- Smoke‑Test: `smoketest` gegen öffentliche URL oder `http://host:80`

## Hinweise
- Frontend **muss** aus `frontend/dist` serviert werden (im Image: `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` sind Pflicht.
- GPU: `compose.prod.yml`; CPU‑Fallback: `compose.cpu.yml`.
