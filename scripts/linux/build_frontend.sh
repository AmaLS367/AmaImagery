#!/usr/bin/env bash
set -euo pipefail
pushd frontend >/dev/null
if command -v pnpm >/dev/null; then
  pnpm install --frozen-lockfile
  pnpm build
elif command -v npm >/dev/null; then
  npm ci
  npm run build
else
  echo "npm/pnpm not found"; exit 1
fi
popd >/dev/null
echo "[build_frontend] dist ready at frontend/dist"
