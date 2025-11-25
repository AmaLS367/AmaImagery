# デプロイスクリプト — 使い方

## 前提条件
- Docker + Docker Compose
- Node.js（npm または pnpm）— フロントエンドのビルド用
- NVIDIA ドライバー + `nvidia-smi`（GPU プロファイルのみ）

## 構成
- `docker/compose.local.yml` — 開発スタック（api + redis + postgres + nginx）
- `docker/compose.prod.yml` — 本番相当のスタック（GPU 予約）
- `docker/compose.cpu.yml` — CPU フォールバック
- `docker/.env.*.example` — 環境テンプレート
- `docker/nginx.conf` — 静的配信 + API プロキシ
- `scripts/linux/*` — Bash スクリプト（Linux）
- `scripts/macos/*` — Bash スクリプト（macOS）
- `scripts/windows/*` — PowerShell スクリプト（Windows）

## 典型的なフロー（Linux/macOS）
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# （Alembic を追加したら）
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## 典型的なフロー（Windows）
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# （Alembic を追加したら）
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## 本番相当の実行
- `.env.prod.example` を基に `docker/.env.prod` を作成
- FE をビルド：`build_frontend`（linux/windows）
- 起動：`run_prod`（linux/windows）
- スモークテスト：公開 URL または `http://host:80` で `smoketest`

## 注意
- フロントエンドは **必ず** `frontend/dist` から配信（イメージ内は `/app/static`）。
- `SECRET_KEY`、`MODEL_ID`、`REDIS_URL`、`DATABASE_URL` は必須。
- GPU：`compose.prod.yml`、CPU フォールバック：`compose.cpu.yml`。
