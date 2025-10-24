# GitHub Actions — قائمة الأسرار/المتغيرات (قالب)

لا تحفظ القيم الحقيقية في المستودع. أضفها ضمن **Settings → Secrets and variables → Actions**.

## السجل (الصور)
- `REGISTRY_HOST` — مضيف السجل. أمثلة: `ghcr.io` أو `docker.io`
- `REGISTRY` — مساحة الاسم في السجل. أمثلة: `ghcr.io/<org>` أو `docker.io/<user>`
- `REGISTRY_USER` — مستخدم السجل
- `REGISTRY_TOKEN` — رمز بصلاحية push (PAT لـ GHCR، و access token لـ Docker Hub)

## الوصول إلى الخادم (staging)
- `SSH_HOST` — المضيف
- `SSH_PORT` — المنفذ، مثلًا `22`
- `SSH_USER` — المستخدم، مثلًا `deploy`
- `SSH_KEY` — المفتاح الخاص **(متعدد الأسطر، OpenSSH/PEM)**

## المسارات على الخادم
- `STAGING_COMPOSE_FILE` — مسار compose، مثلًا `/srv/genai/docker/compose.prod.yml`
- `STAGING_ENV_FILE` — مسار ملف `.env`، مثلًا `/srv/genai/.env`
- `STAGING_FRONTEND_DIR` — مجلد ملفّات الواجهة الأمامية النهائيّة، مثلًا `/srv/genai/frontend/dist`

### ملاحظات
- هذه القيم تُقرأ بواسطة **GitHub Actions**. وهي **لا** تُمرَّر إلى ملفات `.env` داخل الحاويات.
- يمنع تخزين `SSH_KEY` داخل ملفات المستودع.
- يوضع ملف `.env` على الخادم، ونموذجه `/.env.prod.example`.
