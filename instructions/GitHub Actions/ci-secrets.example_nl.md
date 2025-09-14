# GitHub Actions — lijst met secrets/variabelen (sjabloon)

Sla **geen** echte waarden op in de repository. Voeg ze toe onder **Settings → Secrets and variables → Actions**.

## Registry (images)
- `REGISTRY_HOST` — registry-host. Voorbeelden: `ghcr.io` of `docker.io`
- `REGISTRY` — namespace in de registry. Voorbeelden: `ghcr.io/<org>` of `docker.io/<user>`
- `REGISTRY_USER` — registry-gebruiker
- `REGISTRY_TOKEN` — token met push-rechten (PAT voor GHCR, access token voor Docker Hub)

## Servertoegang (staging)
- `SSH_HOST` — host
- `SSH_PORT` — poort, bijv. `22`
- `SSH_USER` — gebruiker, bijv. `deploy`
- `SSH_KEY` — privésleutel **(meerregelig, OpenSSH/PEM)**

## Paden op de server
- `STAGING_COMPOSE_FILE` — pad naar compose, bijv. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — pad naar `.env`, bijv. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — map voor het frontend-artifact, bijv. `/srv/genai/frontend/dist`

### Opmerkingen
- Deze waarden worden gelezen door **GitHub Actions**. Ze gaan **niet** in de `.env`-bestanden van containers.
- Sla `SSH_KEY` nooit op in repo-bestanden.
- Op de server staat een `.env`-bestand; het sjabloon is `/.env.prod.example`.
