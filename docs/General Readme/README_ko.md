# genai — 프로젝트 가이드 (한국어)

## 개요

NSFW 이미지 생성 전체 스택 프로젝트입니다.
- 백엔드: Python + FastAPI (포트 8000)
- 프론트엔드: React + TypeScript + Vite (dev 5173)

빠른 시작 (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
cd frontend
npm install
npm run dev
```

개발 중에는 프론트엔드에서 상대 경로 `/generate` 를 사용하세요 (Vite proxy 적용).

---

(자세한 내용은 `README_en.md` 참조.)
