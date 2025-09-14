# 배포 스크립트 — 사용법

## 사전 준비물
- Docker + Docker Compose
- Node.js (npm 또는 pnpm) — 프런트엔드 빌드
- NVIDIA 드라이버 + `nvidia-smi` (GPU 프로필 전용)

## 구조
- `docker/compose.local.yml` — 개발 스택 (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — 프로덕션 유사 스택 (GPU 예약)
- `docker/compose.cpu.yml` — CPU 폴백
- `docker/.env.*.example` — 환경 템플릿
- `docker/nginx.conf` — 정적 파일 + API 프록시
- `scripts/linux/*` — Bash 스크립트 (Linux)
- `scripts/macos/*` — Bash 스크립트 (macOS)
- `scripts/windows/*` — PowerShell 스크립트 (Windows)

## 일반 흐름 (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (Alembic 추가 후)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## 일반 흐름 (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (Alembic 추가 후)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## 프로덕션 유사 실행
- `.env.prod.example` 기반으로 `docker/.env.prod` 작성
- FE 빌드: `build_frontend` (linux/windows)
- 시작: `run_prod` (linux/windows)
- 스모크 테스트: 공개 URL 또는 `http://host:80` 대상으로 `smoketest`

## 노트
- 프런트엔드는 반드시 `frontend/dist`에서 제공되어야 함 (이미지 내 `/app/static`).
- `SECRET_KEY`, `MODEL_ID`, `REDIS_URL`, `DATABASE_URL` 필수.
- GPU: `compose.prod.yml`; CPU 폴백: `compose.cpu.yml`.
