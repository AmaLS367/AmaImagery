# GitHub Actions — 机密/变量清单（模板）

**不要**在仓库中存放真实值。请在 **Settings → Secrets and variables → Actions** 中添加。

## 镜像仓库（Registry）
- `REGISTRY_HOST` — 仓库主机。例如：`ghcr.io` 或 `docker.io`
- `REGISTRY` — 仓库命名空间。例如：`ghcr.io/<org>` 或 `docker.io/<user>`
- `REGISTRY_USER` — 仓库用户
- `REGISTRY_TOKEN` — 具有 push 权限的令牌（GHCR 用 PAT，Docker Hub 用 access token）

## 服务器访问（staging）
- `SSH_HOST` — 主机
- `SSH_PORT` — 端口，如 `22`
- `SSH_USER` — 用户，如 `deploy`
- `SSH_KEY` — 私钥 **（多行，OpenSSH/PEM）**

## 服务器路径
- `STAGING_COMPOSE_FILE` — compose 路径，如 `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — `.env` 路径，如 `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — 前端制品目录，如 `/srv/genai/frontend/dist`

### 说明
- 这些值由 **GitHub Actions** 读取，**不会**注入到容器的 `.env` 文件。
- `SSH_KEY` 切勿保存在仓库文件中。
- 服务器上会放置 `.env` 文件，其模板为 `/.env.prod.example`。
