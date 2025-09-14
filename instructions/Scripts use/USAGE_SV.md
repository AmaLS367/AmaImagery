# Deploymentskript — Användning

## Förkrav
- Docker + Docker Compose
- Node.js (npm eller pnpm) för att bygga frontend
- NVIDIA‑drivrutiner + `nvidia-smi` (endast GPU‑profil)

## Struktur
- `docker/compose.local.yml` — dev‑stack (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — prod‑lik miljö (GPU‑reservation)
- `docker/compose.cpu.yml` — CPU‑fallback
- `docker/.env.*.example` — mallar för miljövariabler
- `docker/nginx.conf` — statiskt + proxy mot API
- `scripts/linux/*` — Bash‑skript (Linux)
- `scripts/macos/*` — Bash‑skript (macOS)
- `scripts/windows/*` — PowerShell‑skript (Windows)

## Typiskt flöde (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (när du lagt till Alembic)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Typiskt flöde (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (när du lagt till Alembic)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Prod‑lik körning
- Fyll i `docker/.env.prod` baserat på `.env.prod.example`
- Bygg FE: `build_frontend` (linux/windows)
- Starta: `run_prod` (linux/windows)
- Rök‑test: `smoketest` mot publik URL eller `http://host:80`

## Noter
- Frontend **måste** serveras från `frontend/dist` (kopieras till `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` är obligatoriska.
- GPU: `compose.prod.yml`; CPU‑fallback: `compose.cpu.yml`.
