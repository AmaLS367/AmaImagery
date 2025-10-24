# GitHub Actions — Liste der Secrets/Variablen (Vorlage)

Speichere **keine** echten Werte im Repository. Hinterlege sie unter **Settings → Secrets and variables → Actions**.

## Registry (Images)
- `REGISTRY_HOST` — Registry-Host. Beispiele: `ghcr.io` oder `docker.io`
- `REGISTRY` — Namespace in der Registry. Beispiele: `ghcr.io/<org>` oder `docker.io/<user>`
- `REGISTRY_USER` — Registry-Benutzer
- `REGISTRY_TOKEN` — Token mit Push-Recht (PAT für GHCR, Access Token für Docker Hub)

## Serverzugang (Staging)
- `SSH_HOST` — Host
- `SSH_PORT` — Port, z. B. `22`
- `SSH_USER` — Benutzer, z. B. `deploy`
- `SSH_KEY` — privater Schlüssel **(mehrzeilig, OpenSSH/PEM)**

## Pfade auf dem Server
- `STAGING_COMPOSE_FILE` — Pfad zu Compose, z. B. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — Pfad zu `.env`, z. B. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — Verzeichnis für das Frontend-Artefakt, z. B. `/srv/genai/frontend/dist`

### Hinweise
- Diese Werte werden von **GitHub Actions** gelesen. Sie landen **nicht** in `.env`-Dateien der Container.
- `SSH_KEY` niemals im Repository speichern.
- Auf dem Server liegt eine `.env`-Datei; ihre Vorlage ist `/.env.prod.example`.
