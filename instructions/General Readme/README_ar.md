# genai — دليل المشروع (العربية)

## نظرة عامة

مشروع كامل لتوليد الصور NSFW.
- الخلفية: Python + FastAPI (المنفذ 8000)
- الواجهة الأمامية: React + TypeScript + Vite (dev على 5173)

بدء سريع (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
cd frontend
npm install
npm run dev
```

استخدم مسارات نسبية (`/generate`) في الواجهة الأمامية ليعمل بروكسي Vite.

(انظر `README_en.md` للمحتوى الكامل.)
