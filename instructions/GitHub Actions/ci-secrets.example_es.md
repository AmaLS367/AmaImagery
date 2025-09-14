# GitHub Actions — lista de secretos/variables (plantilla)

**No** guardes valores reales en el repositorio. Añádelos en **Settings → Secrets and variables → Actions**.

## Registro (imágenes)
- `REGISTRY_HOST` — host del registro. Ejemplos: `ghcr.io` o `docker.io`
- `REGISTRY` — espacio de nombres. Ejemplos: `ghcr.io/<org>` o `docker.io/<user>`
- `REGISTRY_USER` — usuario del registro
- `REGISTRY_TOKEN` — token con permiso de push (PAT para GHCR, access token para Docker Hub)

## Acceso al servidor (staging)
- `SSH_HOST` — host
- `SSH_PORT` — puerto, p. ej. `22`
- `SSH_USER` — usuario, p. ej. `deploy`
- `SSH_KEY` — clave privada **(multilínea, OpenSSH/PEM)**

## Rutas en el servidor
- `STAGING_COMPOSE_FILE` — ruta a compose, p. ej. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — ruta a `.env`, p. ej. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — directorio del artefacto de frontend, p. ej. `/srv/genai/frontend/dist`

### Notas
- Estos valores los lee **GitHub Actions**. **No** se inyectan en los `.env` de los contenedores.
- `SSH_KEY` nunca debe almacenarse en archivos del repositorio.
- En el servidor se coloca un `.env`; su plantilla es `/.env.prod.example`.
