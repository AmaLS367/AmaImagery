#!/usr/bin/env bash
set -euo pipefail
echo "[preflight] checking tools..."
command -v docker >/dev/null || { echo "docker not found"; exit 1; }
command -v docker compose >/dev/null || { echo "docker compose not found"; exit 1; }

PROFILE="${1:-local}" # local|prod|cpu
if [[ "$PROFILE" != "cpu" ]]; then
  if command -v nvidia-smi >/dev/null; then
    echo "[preflight] GPU present:"; nvidia-smi -L || true
  else
    echo "[preflight] nvidia-smi not found (ok for cpu/local)"
  fi
fi

echo "[preflight] checking env files..."
test -f docker/.env.local || cp docker/.env.local.example docker/.env.local
test -f docker/.env.prod  || cp docker/.env.prod.example  docker/.env.prod

echo "[preflight] checking frontend dist..."
if [[ ! -d frontend/dist ]]; then
  echo "[preflight] dist missing, run scripts/macos/build_frontend.sh"
fi

echo "[preflight] ok"
