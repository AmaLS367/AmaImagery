# Script di deploy — Utilizzo

## Prerequisiti
- Docker + Docker Compose
- Node.js (npm o pnpm) per buildare il frontend
- Driver NVIDIA + `nvidia-smi` (solo profilo GPU)

## Struttura
- `docker/compose.local.yml` — stack di sviluppo (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — stack simil‑prod (prenotazione GPU)
- `docker/compose.cpu.yml` — fallback CPU
- `docker/.env.*.example` — template di ambiente
- `docker/nginx.conf` — statici + proxy verso API
- `scripts/linux/*` — script Bash (Linux)
- `scripts/macos/*` — script Bash (macOS)
- `scripts/windows/*` — script PowerShell (Windows)

## Flusso tipico (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (una volta aggiunto Alembic)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Flusso tipico (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (una volta aggiunto Alembic)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Esecuzione simil‑prod
- Compila `docker/.env.prod` partendo da `.env.prod.example`
- Build FE: `build_frontend` (linux/windows)
- Avvio: `run_prod` (linux/windows)
- Smoke test: `smoketest` su URL pubblico oppure `http://host:80`

## Note
- Il frontend **deve** essere servito da `frontend/dist` (copiato in `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` sono obbligatori.
- GPU: `compose.prod.yml`; fallback CPU: `compose.cpu.yml`.
