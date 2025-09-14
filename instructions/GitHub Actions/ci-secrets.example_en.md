# GitHub Actions — secrets/variables list (template)

Do **not** store real values in the repository. Add them in **Settings → Secrets and variables → Actions**.

## Registry (images)
- `REGISTRY_HOST` — registry host. Examples: `ghcr.io` or `docker.io`
- `REGISTRY` — namespace in the registry. Examples: `ghcr.io/<org>` or `docker.io/<user>`
- `REGISTRY_USER` — registry user
- `REGISTRY_TOKEN` — token with push permission (PAT for GHCR, access token for Docker Hub)

## Server access (staging)
- `SSH_HOST` — host
- `SSH_PORT` — port, e.g. `22`
- `SSH_USER` — user, e.g. `deploy`
- `SSH_KEY` — private key **(multiline, OpenSSH/PEM)**

## Paths on the server
- `STAGING_COMPOSE_FILE` — path to compose, e.g. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — path to `.env`, e.g. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — directory for frontend artifact, e.g. `/srv/genai/frontend/dist`

### Notes
- These values are read by **GitHub Actions**. They do **not** go into container `.env` files.
- `SSH_KEY` must never be stored in repository files.
- A `.env` file is placed on the server; its template is `/.env.prod.example`.
