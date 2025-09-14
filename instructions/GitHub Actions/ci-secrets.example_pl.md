# GitHub Actions — lista sekretów/zmiennych (szablon)

**Nie** przechowuj prawdziwych wartości w repozytorium. Dodaj je w **Settings → Secrets and variables → Actions**.

## Rejestr (obrazy)
- `REGISTRY_HOST` — host rejestru. Przykłady: `ghcr.io` lub `docker.io`
- `REGISTRY` — przestrzeń nazw w rejestrze. Przykłady: `ghcr.io/<org>` lub `docker.io/<user>`
- `REGISTRY_USER` — użytkownik rejestru
- `REGISTRY_TOKEN` — token z prawem push (PAT dla GHCR, access token dla Docker Hub)

## Dostęp do serwera (staging)
- `SSH_HOST` — host
- `SSH_PORT` — port, np. `22`
- `SSH_USER` — użytkownik, np. `deploy`
- `SSH_KEY` — klucz prywatny **(wielowierszowy, OpenSSH/PEM)**

## Ścieżki na serwerze
- `STAGING_COMPOSE_FILE` — ścieżka do compose, np. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — ścieżka do `.env`, np. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — katalog artefaktu frontend, np. `/srv/genai/frontend/dist`

### Uwagi
- Te wartości czyta **GitHub Actions**. **Nie** trafiają do plików `.env` kontenerów.
- `SSH_KEY` nigdy nie powinien być przechowywany w plikach repozytorium.
- Na serwerze umieszczony jest plik `.env`; jego szablon to `/.env.prod.example`.
