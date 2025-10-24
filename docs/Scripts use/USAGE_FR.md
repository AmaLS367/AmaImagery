# Scripts de déploiement — Utilisation

## Prérequis
- Docker + Docker Compose
- Node.js (npm ou pnpm) pour construire le frontend
- Pilotes NVIDIA + `nvidia-smi` (profil GPU uniquement)

## Structure
- `docker/compose.local.yml` — pile dev (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — environnement proche prod (réservation GPU)
- `docker/compose.cpu.yml` — repli CPU
- `docker/.env.*.example` — modèles d’environnement
- `docker/nginx.conf` — statiques + proxy vers l’API
- `scripts/linux/*` — scripts Bash (Linux)
- `scripts/macos/*` — scripts Bash (macOS)
- `scripts/windows/*` — scripts PowerShell (Windows)

## Flux typique (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (une fois Alembic ajouté)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Flux typique (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (une fois Alembic ajouté)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Exécution proche prod
- Renseigner `docker/.env.prod` à partir de `.env.prod.example`
- Construire le FE : `build_frontend` (linux/windows)
- Démarrer : `run_prod` (linux/windows)
- Smoke test : `smoketest` sur l’URL publique ou `http://host:80`

## Notes
- Le frontend **doit** être servi depuis `frontend/dist` (copié dans `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` sont obligatoires.
- GPU : `compose.prod.yml` ; repli CPU : `compose.cpu.yml`.
