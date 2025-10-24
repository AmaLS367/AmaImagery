# GitHub Actions — 시크릿/변수 목록 (템플릿)

실제 값은 리포지토리에 **저장하지 마세요**. **Settings → Secrets and variables → Actions** 에서 추가하세요.

## 레지스트리(이미지)
- `REGISTRY_HOST` — 레지스트리 호스트. 예: `ghcr.io` 또는 `docker.io`
- `REGISTRY` — 레지스트리 네임스페이스. 예: `ghcr.io/<org>` 또는 `docker.io/<user>`
- `REGISTRY_USER` — 레지스트리 사용자
- `REGISTRY_TOKEN` — push 권한 토큰 (GHCR: PAT, Docker Hub: access token)

## 서버 접근 (staging)
- `SSH_HOST` — 호스트
- `SSH_PORT` — 포트, 예: `22`
- `SSH_USER` — 사용자, 예: `deploy`
- `SSH_KEY` — 개인키 **(다중 행, OpenSSH/PEM)**

## 서버 경로
- `STAGING_COMPOSE_FILE` — compose 경로, 예: `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — `.env` 경로, 예: `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — 프런트엔드 아티팩트 디렉터리, 예: `/srv/genai/frontend/dist`

### 참고
- 이 값들은 **GitHub Actions** 가 읽습니다. 컨테이너 `.env` 파일로는 **들어가지 않습니다**.
- `SSH_KEY` 는 리포지토리 파일에 절대 저장하지 마세요.
- 서버에는 `.env` 파일이 배치되며, 템플릿은 `/.env.prod.example` 입니다.
