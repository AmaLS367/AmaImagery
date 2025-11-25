# GitHub Actions — elenco di secret/variabili (template)

**Non** archiviare valori reali nel repository. Aggiungili in **Settings → Secrets and variables → Actions**.

## Registry (immagini)
- `REGISTRY_HOST` — host del registry. Esempi: `ghcr.io` o `docker.io`
- `REGISTRY` — namespace nel registry. Esempi: `ghcr.io/<org>` o `docker.io/<user>`
- `REGISTRY_USER` — utente del registry
- `REGISTRY_TOKEN` — token con permesso di push (PAT per GHCR, access token per Docker Hub)

## Accesso al server (staging)
- `SSH_HOST` — host
- `SSH_PORT` — porta, es. `22`
- `SSH_USER` — utente, es. `deploy`
- `SSH_KEY` — chiave privata **(multilinea, OpenSSH/PEM)**

## Percorsi sul server
- `STAGING_COMPOSE_FILE` — percorso a compose, es. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — percorso a `.env`, es. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — directory per l’artefatto frontend, es. `/srv/genai/frontend/dist`

### Note
- Questi valori sono letti da **GitHub Actions**. **Non** finiscono nei file `.env` dei container.
- `SSH_KEY` non va mai salvata nei file del repository.
- Sul server viene posto un file `.env`; il relativo template è `/.env.prod.example`.
