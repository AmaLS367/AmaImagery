#!/usr/bin/env bash
set -euo pipefail
API="${1:-http://localhost:8000}"
EXPECTED_PROVIDER="${2:-${SMOKE_EXPECT_PROVIDER:-}}"
SMOKE_EMAIL="${SMOKE_EMAIL:-smoke-$(date +%s)@example.com}"
SMOKE_PASSWORD="${SMOKE_PASSWORD:-pass12345}"
SMOKE_USERNAME="${SMOKE_USERNAME:-smoke$(date +%s)}"

json_field() {
  local field="$1"
  python -c '
import json
import sys

field = sys.argv[1]
payload = json.load(sys.stdin)
value = payload
for part in field.split("."):
    if isinstance(value, dict):
        value = value.get(part)
    else:
        value = None
        break
if value is None:
    print("")
elif isinstance(value, (dict, list)):
    print(json.dumps(value))
else:
    print(value)
' "$field"
}

auth_headers=()

echo "[smoke] healthz"
curl -fsS "$API/api/v1/healthz" >/dev/null

echo "[smoke] register"
register_status=$(curl -sS -o /tmp/ama_smoke_register.json -w "%{http_code}" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$SMOKE_EMAIL\",\"password\":\"$SMOKE_PASSWORD\",\"username\":\"$SMOKE_USERNAME\"}" \
  "$API/api/v1/auth/register")
if [[ "$register_status" != "201" && "$register_status" != "409" ]]; then
  echo "Unexpected register status: $register_status"
  cat /tmp/ama_smoke_register.json
  exit 1
fi

echo "[smoke] login"
LOGIN=$(curl -fsS -H 'Content-Type: application/json' \
  -d "{\"identifier\":\"$SMOKE_EMAIL\",\"password\":\"$SMOKE_PASSWORD\"}" \
  "$API/api/v1/auth/login")
TOKEN=$(printf '%s' "$LOGIN" | json_field access_token)
if [[ -z "$TOKEN" ]]; then
  echo "$LOGIN"
  exit 1
fi
auth_headers=(-H "Authorization: Bearer $TOKEN")

echo "[smoke] generate"
TASK=$(curl -fsS "${auth_headers[@]}" -H 'Content-Type: application/json' -d '{"prompt":"a cat","steps":5,"guidance_scale":4,"width":256,"height":256,"seed":1}' "$API/api/v1/images/generate")
TASK_ID=$(printf '%s' "$TASK" | json_field task_id)
if [[ -z "$TASK_ID" ]]; then
  echo "$TASK"
  exit 1
fi
URL=""
TERMINAL_PROVIDER=""
for _ in $(seq 1 60); do
  STATUS=$(curl -fsS "${auth_headers[@]}" "$API/api/v1/images/status/$TASK_ID")
  STATE=$(printf '%s' "$STATUS" | json_field status)
  PROVIDER=$(printf '%s' "$STATUS" | json_field provider_name)
  if [[ "$STATE" == "completed" ]]; then
    URL=$(printf '%s' "$STATUS" | json_field image_url)
    TERMINAL_PROVIDER="$PROVIDER"
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
if [[ -n "$EXPECTED_PROVIDER" && "$TERMINAL_PROVIDER" != "$EXPECTED_PROVIDER" ]]; then
  echo "Expected provider '$EXPECTED_PROVIDER' but got '$TERMINAL_PROVIDER'"
  exit 1
fi
echo "[smoke] file $URL"
curl -fsS "${auth_headers[@]}" -o /dev/null "$API$URL"
echo "[smoke] history"
HISTORY=$(curl -fsS "${auth_headers[@]}" "$API/api/v1/users/me/generations?limit=20&offset=0")
HISTORY_TASK_ID=$(printf '%s' "$HISTORY" | python - "$TASK_ID" <<'PY'
import json
import sys

task_id = sys.argv[1]
payload = json.load(sys.stdin)
for item in payload.get("items", []):
    if str(item.get("task_id")) == task_id:
        print(task_id)
        break
PY
)
if [[ "$HISTORY_TASK_ID" != "$TASK_ID" ]]; then
  echo "History did not include task $TASK_ID"
  exit 1
fi
if [[ -n "$EXPECTED_PROVIDER" ]]; then
  HISTORY_PROVIDER=$(printf '%s' "$HISTORY" | python - "$TASK_ID" <<'PY'
import json
import sys

task_id = sys.argv[1]
payload = json.load(sys.stdin)
for item in payload.get("items", []):
    if str(item.get("task_id")) == task_id:
        print(item.get("provider_name") or "")
        break
PY
)
  if [[ "$HISTORY_PROVIDER" != "$EXPECTED_PROVIDER" ]]; then
    echo "History provider mismatch: expected '$EXPECTED_PROVIDER', got '$HISTORY_PROVIDER'"
    exit 1
  fi
fi
echo "[smoke] ok"
