#!/usr/bin/env bash
set -euo pipefail
API="${1:-http://localhost:8000}"
echo "[smoke] healthz"
curl -fsS "$API/healthz" >/dev/null
echo "[smoke] generate"
RESP=$(curl -fsS -H 'Content-Type: application/json' -d '{"prompt":"a cat","steps":5,"guidance_scale":4,"width":256,"height":256,"seed":1}' "$API/generate")
PATH_FIELD=$(echo "$RESP" | sed -n 's/.*"path":"\([^"]*\)".*/\1/p')
SIG=$(echo "$RESP" | sed -n 's/.*"sig":"\([^"]*\)".*/\1/p')
EXP=$(echo "$RESP" | sed -n 's/.*"exp":\([0-9]*\).*/\1/p')
if [[ -n "$SIG" && -n "$EXP" ]]; then
  URL="$API/file?path=$PATH_FIELD&sig=$SIG&exp=$EXP"
else
  URL="$API/file?path=$PATH_FIELD"
fi
echo "[smoke] file $URL"
curl -fsS -o /dev/null "$URL"
echo "[smoke] ok"
