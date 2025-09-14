# Scripts de deploy — Uso

## Pré‑requisitos
- Docker + Docker Compose
- Node.js (npm ou pnpm) para build do frontend
- Drivers NVIDIA + `nvidia-smi` (apenas perfil GPU)

## Estrutura
- `docker/compose.local.yml` — stack de desenvolvimento (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — stack tipo produção (reserva de GPU)
- `docker/compose.cpu.yml` — fallback de CPU
- `docker/.env.*.example` — templates de ambiente
- `docker/nginx.conf` — estáticos + proxy do API
- `scripts/linux/*` — scripts Bash (Linux)
- `scripts/macos/*` — scripts Bash (macOS)
- `scripts/windows/*` — scripts PowerShell (Windows)

## Fluxo típico (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (quando adicionar Alembic)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Fluxo típico (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (quando adicionar Alembic)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Execução tipo produção
- Preencha `docker/.env.prod` com base em `.env.prod.example`
- Build do FE: `build_frontend` (linux/windows)
- Início: `run_prod` (linux/windows)
- Smoke test: `smoketest` na URL pública ou `http://host:80`

## Observações
- O frontend **deve** ser servido de `frontend/dist` (copiado para `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` são obrigatórios.
- GPU: `compose.prod.yml`; fallback de CPU: `compose.cpu.yml`.
