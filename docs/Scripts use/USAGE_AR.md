# سكربتات النشر — طريقة الاستخدام

## المتطلبات المسبقة
- Docker و Docker Compose
- Node.js (npm أو pnpm) لبناء الواجهة الأمامية
- تعريفات NVIDIA و `nvidia-smi` (ملف تعريف GPU فقط)

## البنية
- `docker/compose.local.yml` — حزمة التطوير (api + redis + postgres + nginx)
- `docker/compose.prod.yml` — بيئة شبيهة بالإنتاج (حجز GPU)
- `docker/compose.cpu.yml` — بديل CPU
- `docker/.env.*.example` — قوالب المتغيرات
- `docker/nginx.conf` — ملفات ثابتة + وكيل لواجهة الـ API
- `scripts/linux/*` — سكربتات Bash (Linux)
- `scripts/macos/*` — سكربتات Bash (macOS)
- `scripts/windows/*` — سكربتات PowerShell (Windows)

## التدفق المعتاد (Linux/macOS)
```bash
scripts/linux/build_frontend.sh
scripts/linux/preflight.sh local
scripts/linux/run_local.sh
# (عند إضافة Alembic)
scripts/linux/migrate.sh && scripts/linux/seed.sh
scripts/linux/smoketest.sh
```

## التدفق المعتاد (Windows)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build_frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/preflight.ps1 -Profile local
powershell -ExecutionPolicy Bypass -File scripts/windows/run_local.ps1
# (عند إضافة Alembic)
powershell -ExecutionPolicy Bypass -File scripts/windows/migrate.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/seed.ps1
powershell -ExecutionPolicy Bypass -File scripts/windows/smoketest.ps1
```

## تشغيل شبيه بالإنتاج
- املأ `docker/.env.prod` بناءً على `.env.prod.example`
- ابنِ الواجهة الأمامية: `build_frontend` (linux/windows)
- البدء: `run_prod` (linux/windows)
- اختبار دخاني: `smoketest` على العنوان العام أو `http://host:80`

## ملاحظات
- يجب خدمة الواجهة الأمامية من `frontend/dist` (تُنسخ إلى `/app/static`).
- `SECRET_KEY` و `MODEL_ID` و `REDIS_URL` و `DATABASE_URL` مطلوبة.
- GPU: استخدم `compose.prod.yml`؛ بديل CPU: `compose.cpu.yml`.
