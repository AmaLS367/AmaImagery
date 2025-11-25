# GitHub Actions — список секретов/переменных (шаблон)

Не хранить реальные значения в репозитории. Внести в **Settings → Secrets and variables → Actions**.

## Registry (образы)
- `REGISTRY_HOST` — хост реестра. Примеры: `ghcr.io` или `docker.io`
- `REGISTRY` — namespace в реестре. Примеры: `ghcr.io/<org>` или `docker.io/<user>`
- `REGISTRY_USER` — пользователь в реестре
- `REGISTRY_TOKEN` — токен с правом push (PAT для GHCR, access token для Docker Hub)

## Доступ на сервер (staging)
- `SSH_HOST` — хост
- `SSH_PORT` — порт, напр. `22`
- `SSH_USER` — пользователь, напр. `deploy`
- `SSH_KEY` — приватный ключ **(многострочный, OpenSSH/PEM)**

## Пути на сервере
- `STAGING_COMPOSE_FILE` — путь к compose, напр. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — путь к `.env`, напр. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — директория для артефакта фронта, напр. `/srv/genai/frontend/dist`

### Примечания
- Эти значения читает **GitHub Actions**. Они **не** идут в `.env` контейнеров.
- `SSH_KEY` никогда не хранить в файлах репозитория.
- На сервер кладётся файл `.env`, его шаблон — `/.env.prod.example`.
