# genai — Guide du projet (Français)

## Aperçu

Application de génération d'images. Contient :
- Backend : FastAPI (Python) sur le port 8000.
- Frontend : React + TypeScript + Vite sur le port 5173 (dev).

Ce guide couvre le démarrage, l'architecture, le flux de génération et le débogage.

---

## Démarrage rapide

Prérequis : Python 3.11+, Node.js 18+

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
cd frontend
npm install
npm run dev
```

Note : utilisez des chemins relatifs (`/generate`) dans le frontend pour bénéficier du proxy Vite.

---

## Flux de génération

1. L'utilisateur clique sur "Générer" → `Generate.tsx` crée le payload.
2. Le frontend met la tâche dans `RequestQueue`.
3. `generateJSON` envoie POST à `/generate`.
4. Vite proxy redirige vers `http://localhost:8000/generate`.
5. Le backend traite et retourne `{path, prompt_hash}`.
6. Le frontend affiche l'image via `/file?path=`.

---

## Débogage

- Si aucun appel n'arrive au backend : vérifier la Console et l'onglet Network du navigateur.
- Si le backend répond mais le frontend échoue : tester avec curl et vérifier la configuration du proxy.

---

Je peux générer un diagramme mermaid ou un diagramme ASCII du flux si souhaité.
