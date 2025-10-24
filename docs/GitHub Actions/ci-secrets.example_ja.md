# GitHub Actions — シークレット/変数一覧（テンプレート）

実値をリポジトリに**保管しないでください**。**Settings → Secrets and variables → Actions** に登録します。

## レジストリ（イメージ）
- `REGISTRY_HOST` — レジストリホスト。例：`ghcr.io` または `docker.io`
- `REGISTRY` — レジストリ内の名前空間。例：`ghcr.io/<org>` または `docker.io/<user>`
- `REGISTRY_USER` — レジストリユーザー
- `REGISTRY_TOKEN` — push 権限付きトークン（GHCR は PAT、Docker Hub は access token）

## サーバーアクセス（staging）
- `SSH_HOST` — ホスト
- `SSH_PORT` — ポート（例：`22`）
- `SSH_USER` — ユーザー（例：`deploy`）
- `SSH_KEY` — 秘密鍵 **（複数行、OpenSSH/PEM）**

## サーバー上のパス
- `STAGING_COMPOSE_FILE` — compose のパス（例：`/srv/genai/docker/compose.prod.yml`）
- `STAGING_ENV_FILE` — `.env` のパス（例：`/srv/genai/.env`）
- `STAGING_FRONTEND_DIR` — フロントエンド成果物のディレクトリ（例：`/srv/genai/frontend/dist`）

### 備考
- これらの値は **GitHub Actions** が読み込みます。コンテナの `.env` には**入りません**。
- `SSH_KEY` をレポジトリ内のファイルに保存してはいけません。
- サーバーには `.env` ファイルが配置されます。テンプレートは `/.env.prod.example` です。
