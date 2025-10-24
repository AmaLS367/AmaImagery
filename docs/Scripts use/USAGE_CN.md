# 部署脚本 — 使用说明

## 前置条件
- Docker 与 Docker Compose
- Node.js（npm 或 pnpm）用于构建前端
- NVIDIA 驱动与 `nvidia-smi`（仅 GPU 配置）

## 结构
- `docker/compose.local.yml` — 开发栈（api + redis + postgres + nginx）
- `docker/compose.prod.yml` — 类生产环境（GPU 预留）
- `docker/compose.cpu.yml` — CPU 回退
- `docker/.env.*.example` — 环境模板
- `docker/nginx.conf` — 静态资源 + API 代理
- `scripts/linux/*` — Bash 脚本（Linux）
- `scripts/macos/*` — Bash 脚本（macOS）
- `scripts/windows/*` — PowerShell 脚本（Windows）

## 典型流程（Linux/macOS）
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# （添加 Alembic 后）
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## 典型流程（Windows）
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# （添加 Alembic 后）
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## 类生产运行
- 基于 `.env.prod.example` 填写 `docker/.env.prod`
- 构建前端：`build_frontend`（linux/windows）
- 启动：`run_prod`（linux/windows）
- 冒烟测试：对公共 URL 或 `http://host:80` 执行 `smoketest`

## 说明
- 前端必须从 `frontend/dist` 提供（复制到镜像 `/app/static`）。
- 必填变量：`SECRET_KEY`、`MODEL_ID`、`REDIS_URL`、`DATABASE_URL`。
- GPU 用 `compose.prod.yml`；CPU 回退用 `compose.cpu.yml`。
