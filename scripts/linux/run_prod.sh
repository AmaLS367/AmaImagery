#!/usr/bin/env bash
set -euo pipefail
scripts/linux/preflight.sh prod
scripts/linux/build_frontend.sh
docker compose -f docker/compose.prod.yml --env-file docker/.env.prod up -d --build
echo "[run_prod] nginx :80 → api :8000"
