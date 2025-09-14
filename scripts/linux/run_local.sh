#!/usr/bin/env bash
set -euo pipefail
scripts/linux/preflight.sh local
docker compose -f docker/compose.local.yml up -d --build
echo "[run_local] UI http://localhost:8080 / API :8000"
