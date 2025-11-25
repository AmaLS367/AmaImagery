# GitHub Actions — gizli değişkenler/değişkenler listesi (şablon)

Gerçek değerleri depoda **saklamayın**. **Settings → Secrets and variables → Actions** altında tanımlayın.

## Kayıt (imajlar)
- `REGISTRY_HOST` — registry hostu. Örn: `ghcr.io` veya `docker.io`
- `REGISTRY` — registry içindeki namespace. Örn: `ghcr.io/<org>` veya `docker.io/<user>`
- `REGISTRY_USER` — registry kullanıcısı
- `REGISTRY_TOKEN` — push yetkili token (GHCR için PAT, Docker Hub için access token)

## Sunucu erişimi (staging)
- `SSH_HOST` — host
- `SSH_PORT` — port, örn. `22`
- `SSH_USER` — kullanıcı, örn. `deploy`
- `SSH_KEY` — özel anahtar **(çok satırlı, OpenSSH/PEM)**

## Sunucudaki yollar
- `STAGING_COMPOSE_FILE` — compose yolu, örn. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — `.env` yolu, örn. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — frontend artefakt klasörü, örn. `/srv/genai/frontend/dist`

### Notlar
- Bu değerler **GitHub Actions** tarafından okunur. Konteyner `.env` dosyalarına **gitmez**.
- `SSH_KEY` depo dosyalarında asla saklanmamalıdır.
- Sunucuya bir `.env` dosyası konur; şablonu `/.env.prod.example`.
