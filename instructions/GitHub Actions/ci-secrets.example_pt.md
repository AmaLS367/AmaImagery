# GitHub Actions — lista de segredos/variáveis (modelo)

**Não** armazene valores reais no repositório. Cadastre-os em **Settings → Secrets and variables → Actions**.

## Registry (imagens)
- `REGISTRY_HOST` — host do registry. Exemplos: `ghcr.io` ou `docker.io`
- `REGISTRY` — namespace no registry. Exemplos: `ghcr.io/<org>` ou `docker.io/<user>`
- `REGISTRY_USER` — usuário do registry
- `REGISTRY_TOKEN` — token com permissão de push (PAT para GHCR, access token para Docker Hub)

## Acesso ao servidor (staging)
- `SSH_HOST` — host
- `SSH_PORT` — porta, ex. `22`
- `SSH_USER` — usuário, ex. `deploy`
- `SSH_KEY` — chave privada **(multilinha, OpenSSH/PEM)**

## Caminhos no servidor
- `STAGING_COMPOSE_FILE` — caminho do compose, ex. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — caminho do `.env`, ex. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — diretório do artefato do frontend, ex. `/srv/genai/frontend/dist`

### Observações
- Esses valores são lidos pelo **GitHub Actions**. Eles **não** vão para os `.env` dos containers.
- Nunca armazene o `SSH_KEY` em arquivos do repositório.
- No servidor existe um `.env`; seu template é `/.env.prod.example`.
