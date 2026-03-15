#!/usr/bin/env bash
set -euo pipefail
echo "[preflight] checking tools..."
command -v docker >/dev/null || { echo "docker not found"; exit 1; }
command -v docker compose >/dev/null || { echo "docker compose not found"; exit 1; }

MODE="${1:-local}" # local|prod|cpu
if [[ "$MODE" != "cpu" ]]; then
  if command -v nvidia-smi >/dev/null; then
    echo "[preflight] GPU present:"; nvidia-smi -L || true
  else
    echo "[preflight] nvidia-smi not found (ok for cpu/local)"
  fi
fi

echo "[preflight] checking env files..."
case "$MODE" in
  local|cpu)
    test -f docker/.env.docker || cp docker/.env.docker.example docker/.env.docker
    ;;
  prod)
    test -f docker/.env.prod || cp docker/.env.prod.example docker/.env.prod
    ;;
  *)
    echo "unsupported mode: $MODE" >&2
    exit 1
    ;;
esac

echo "[preflight] checking frontend dist..."
if [[ ! -d frontend/dist ]]; then
  echo "[preflight] dist missing, run scripts/linux/build_frontend.sh"
fi

echo "[preflight] ok"
