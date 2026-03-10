#!/usr/bin/env bash
set -euo pipefail
API="${1:-http://localhost:8000}"
echo "[smoke] healthz"
curl -fsS "$API/api/v1/healthz" >/dev/null
echo "[smoke] generate"
TASK=$(curl -fsS -H 'Content-Type: application/json' -d '{"prompt":"a cat","steps":5,"guidance_scale":4,"width":256,"height":256,"seed":1}' "$API/api/v1/images/generate")
TASK_ID=$(echo "$TASK" | sed -n 's/.*"task_id":"\([^"]*\)".*/\1/p')
if [[ -z "$TASK_ID" ]]; then
  echo "$TASK"
  exit 1
fi
URL=""
for _ in $(seq 1 60); do
  STATUS=$(curl -fsS "$API/api/v1/images/status/$TASK_ID")
  STATE=$(echo "$STATUS" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  if [[ "$STATE" == "completed" ]]; then
    URL=$(echo "$STATUS" | sed -n 's/.*"image_url":"\([^"]*\)".*/\1/p' | sed 's#\\/#/#g')
    break
  fi
  if [[ "$STATE" == "failed" ]]; then
    echo "$STATUS"
    exit 1
  fi
  sleep 2
done
if [[ -z "$URL" ]]; then
  echo "Timed out waiting for generation $TASK_ID"
  exit 1
fi
echo "[smoke] file $URL"
curl -fsS -o /dev/null "$API$URL"
echo "[smoke] ok"
