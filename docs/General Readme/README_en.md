# genai — Project Guide (English)

## Overview

This repository is an end-to-end NSFW image generation project. It contains:
- Backend: Python + FastAPI, runs on port 8000 by default and exposes endpoints for health checks, generation, and serving files.
- Frontend: React + TypeScript + Vite, runs on port 5173 in development. UI has pages for generation, history, and settings.

This guide covers architecture, how to run locally, logging, the generation flow, debugging, and Docker notes + Security Deploy Checklist.

---

## Quick start (development)

Requirements:
- Python 3.11+
- Node.js 18+ and npm
- (Optional) NVIDIA GPU and drivers if you want to run heavy model code locally

Commands (Windows PowerShell):

```powershell
# Activate venv (already created in repo):
.\.venv\Scripts\Activate.ps1

# Install backend dependencies (if not installed):
pip install -r requirements.txt

# Run backend (dev):
python run.py

# Frontend (from repo root):
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

Notes:
- The repo includes a Vite proxy that forwards `/generate`, `/health`, and `/file` calls to the backend (default `http://localhost:8000`). When developing, use relative paths (`/generate`) in the frontend code so Vite's proxy handles routing.

---

## Project structure (important files)

- `run.py` — backend entrypoint (starts Uvicorn / FastAPI)
- `app/` — backend package (API routes, config, logging, inference pipeline)
  - `app/server.py` — FastAPI app and routes
  - `app/inference/pipeline.py` — generation pipeline
  - `app/logging_setup.py` — log configuration
- `frontend/` — React app
  - `frontend/src/lib/api.ts` — wrapper helpers for fetch requests (generateJSON, health)
  - `frontend/src/pages/Generate.tsx` — main generation UI and handler
  - `frontend/src/lib/queue.ts` — RequestQueue used to serialize/cancel requests
  - `frontend/vite.config.ts` — dev server + proxy configuration
  - `frontend/.env` — local env options for Vite
- `models/` — pre-downloaded model weights (large binary files)
- `logs/` — runtime logs (access, app, errors, generations, metrics, prompts)

---

## How generation works (end-to-end)

1. User clicks "Generate" in the UI (`Generate.tsx`).
2. Frontend builds a `GeneratePayload` JSON: prompt, negative_prompt, steps, guidance_scale, width/height, seed, optional `ref_image_b64`, `ip_scale`.
3. Frontend enqueues a task into `RequestQueue.run()`. The task calls `generateJSON(payload, signal)`.
4. `generateJSON` calls `fetch('/generate', {method: 'POST', body: JSON.stringify(payload)})`.
   - In development, Vite proxies `/generate` to `http://localhost:8000/generate`.
5. Backend receives the request and schedules the inference pipeline. When done, it returns a JSON with `path`, optional `prompt_hash`, and `corrections`.
6. Frontend receives the path and shows the generated image using `/file?path=...` endpoint.
7. The result is added to local history and optionally persisted in `logs/generations`.

---

## Logging

Backend logging:
- `app/logging_setup.py` configures structured logs (JSONL) written into `logs/app/`, `logs/errors/`, etc.
- Generation events, timestamps, and errors go to `logs/generations` and `logs/errors`.

Frontend logging:
- Console logs in `Generate.tsx` and `api.ts` were added for debugging.
- Use browser DevTools Network tab to see requests and responses.

---

## Common troubleshooting steps

No request reaches backend when pressing the button:
1. Open browser DevTools → Console and Network.
2. Ensure clicking logs appear in Console (we log `Button clicked`, `gen() function called`). If console logs don't appear, the click handler isn't running. Check for overlays or disabled buttons.
3. In Network tab, filter for `generate` and press the button. If no network request — the frontend did not call fetch.
4. If a request is present but CORS/302/SSL issues occur, check `vite.config.ts` proxy and `frontend/.env`.
5. Check backend logs (tail `logs/app/*.jsonl` or terminal where `run.py` runs). A valid POST will show a `/generate` request.
6. Test directly with curl to confirm backend is reachable:

```powershell
curl -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{"prompt":"test","steps":1,"guidance_scale":1,"width":256,"height":256,"seed":1}'
```

If that works, the problem is on the frontend (proxy, API path, or queue).

---

## Dev tips and debugging

- If Vite tries to connect via `wss://localhost/` and fails, change HMR config in `vite.config.ts` to `hmr: { protocol: 'ws' }`.
- Use `console.log` in `Generate.tsx` and `api.ts` to trace execution. Look for `Making request to:` and `Response data:` logs.
- Confirm `RequestQueue` behavior: it should not abort the newly pushed task. See `frontend/src/lib/queue.ts`.

---

## API: contract

`POST /generate` — request body example
```json
{
  "prompt": "anime portrait",
  "negative_prompt": null,
  "steps": 28,
  "guidance_scale": 7,
  "width": 896,
  "height": 1152,
  "seed": null,
  "ref_image_b64": null,
  "ip_scale": 0.6
}
```

Response example
```json
{
  "path": "outputs/abcdef.png",
  "prompt_hash": "deadbeef",
  "corrections": [["low quality","remove low quality"]]
}
```

`GET /health` → `{ "ok": true }`
`GET /file?path=...` → serves a static image

---

## Docker

The repository includes a `Dockerfile` that installs Python, dependencies and runs `python run.py`:

```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
# ... installs
EXPOSE 8000
CMD ["python3", "run.py"]
```

This image expects models to be available in `models/` or mounted into the container.

---

## Security & production notes

- For production, serve the frontend statically and the backend behind a proper reverse-proxy (nginx) with TLS.
- Disable debug logs and ensure model weights are secured.
- Consider authentication and rate-limiting on `/generate` to avoid abuse.

---

## Contributing

- Keep frontend calls relative (`/generate`) to allow dev proxying.
- Add unit tests for `RequestQueue` and for small UI behavior.
- If changing endpoints, update `frontend/src/lib/api.ts` accordingly.

---

