$ErrorActionPreference='Stop'
docker compose -f docker/compose.local.yml exec -T api python - << 'PY'
from app.ops.seed import run_seed
run_seed()
PY
