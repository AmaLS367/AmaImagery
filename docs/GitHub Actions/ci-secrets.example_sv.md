# GitHub Actions — lista över secrets/variabler (mall)

Spara **inte** riktiga värden i repot. Lägg in dem under **Settings → Secrets and variables → Actions**.

## Registry (images)
- `REGISTRY_HOST` — registry-värd. Exempel: `ghcr.io` eller `docker.io`
- `REGISTRY` — namespace i registret. Exempel: `ghcr.io/<org>` eller `docker.io/<user>`
- `REGISTRY_USER` — registry-användare
- `REGISTRY_TOKEN` — token med push-rättighet (PAT för GHCR, access token för Docker Hub)

## Serveråtkomst (staging)
- `SSH_HOST` — värd
- `SSH_PORT` — port, t.ex. `22`
- `SSH_USER` — användare, t.ex. `deploy`
- `SSH_KEY` — privat nyckel **(flerradig, OpenSSH/PEM)**

## Sökvägar på servern
- `STAGING_COMPOSE_FILE` — sökväg till compose, t.ex. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — sökväg till `.env`, t.ex. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — katalog för frontend‑artefakt, t.ex. `/srv/genai/frontend/dist`

### Noter
- Dessa värden läses av **GitHub Actions**. De hamnar **inte** i containrarnas `.env`.
- `SSH_KEY` får aldrig lagras i repo-filer.
- En `.env`-fil ligger på servern; dess mall är `/.env.prod.example`.
