# GitHub Actions — liste des secrets/variables (modèle)

Ne stockez **pas** de valeurs réelles dans le dépôt. Ajoutez-les dans **Settings → Secrets and variables → Actions**.

## Registry (images)
- `REGISTRY_HOST` — hôte du registre. Ex. : `ghcr.io` ou `docker.io`
- `REGISTRY` — espace de noms du registre. Ex. : `ghcr.io/<org>` ou `docker.io/<user>`
- `REGISTRY_USER` — utilisateur du registre
- `REGISTRY_TOKEN` — jeton avec droit de push (PAT pour GHCR, access token pour Docker Hub)

## Accès serveur (staging)
- `SSH_HOST` — hôte
- `SSH_PORT` — port, ex. `22`
- `SSH_USER` — utilisateur, ex. `deploy`
- `SSH_KEY` — clé privée **(multiligne, OpenSSH/PEM)**

## Chemins sur le serveur
- `STAGING_COMPOSE_FILE` — chemin vers compose, ex. `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — chemin vers `.env`, ex. `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — dossier pour l’artefact frontend, ex. `/srv/genai/frontend/dist`

### Remarques
- Ces valeurs sont lues par **GitHub Actions**. Elles **ne** vont pas dans les fichiers `.env` des conteneurs.
- Ne jamais stocker `SSH_KEY` dans le dépôt.
- Un fichier `.env` est placé sur le serveur ; son modèle est `/.env.prod.example`.
