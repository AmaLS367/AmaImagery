# Dağıtım Scriptleri — Kullanım

## Önkoşullar
- Docker + Docker Compose
- Node.js (npm veya pnpm) — frontend derlemek için
- NVIDIA sürücüleri + `nvidia-smi` (yalnızca GPU profili)

## Yapı
- `docker/compose.local.yml` — geliştirme yığını (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — prod’a benzer ortam (GPU rezervasyonu)
- `docker/compose.cpu.yml` — CPU geri dönüş
- `docker/.env.*.example` — ortam şablonları
- `docker/nginx.conf` — statik + API proxy
- `scripts/linux/*` — Bash scriptleri (Linux)
- `scripts/macos/*` — Bash scriptleri (macOS)
- `scripts/windows/*` — PowerShell scriptleri (Windows)

## Tipik akış (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (Alembic eklediğinde)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## Tipik akış (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (Alembic eklediğinde)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## Prod‑benzeri çalıştırma
- `.env.prod.example` temel alınarak `docker/.env.prod` doldur
- FE derle: `build_frontend` (linux/windows)
- Başlat: `run_prod` (linux/windows)
- Smoke test: genel URL veya `http://host:80` üzerinde `smoketest`

## Notlar
- Frontend **mutlaka** `frontend/dist`’ten servis edilmelidir (imajda: `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` zorunlu.
- GPU: `compose.prod.yml`; CPU dönüş: `compose.cpu.yml`.
