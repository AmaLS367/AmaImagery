# genai — Projektguide (Svenska)

## Översikt

End-to-end projekt för NSFW-bildgenerering.

Kräv:
- Python 3.11+
- Node.js 18+

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
cd frontend
npm install
npm run dev
```

Använd relativa sökvägar (`/generate`) i frontend för att Vite proxy ska vidarebefordra till backend.

(Se `README_en.md` för fullständig info.)
