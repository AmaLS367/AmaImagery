# genai — Projektanleitung (Deutsch)

## Überblick

Dieses Repository ist ein End-to-End NSFW-Bildgenerierungsprojekt. Es enthält:
- Backend: Python + FastAPI, läuft standardmäßig auf Port 8000 und bietet Endpunkte für Health-Checks, Generierung und das Ausliefern von Dateien.
- Frontend: React + TypeScript + Vite, läuft während der Entwicklung auf Port 5173. Die UI enthält Seiten für Generierung, Verlauf und Einstellungen.

Diese Anleitung behandelt Architektur, lokalen Start, Logging, den Generierungsablauf, Debugging und Docker-Hinweise.

---

## Schnellstart (Entwicklung)

Voraussetzungen:
- Python 3.11+
- Node.js 18+ und npm

PowerShell Befehle:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
cd frontend
npm install
npm run dev
# http://localhost:5173 öffnen
```

Hinweis: Verwenden Sie relative Pfade (`/generate`) im Frontend, damit der Vite-Proxy die Weiterleitung an `http://localhost:8000` übernimmt.

---

(Die Datei folgt inhaltlich der englischen README; für Details siehe `README_en.md`.)
