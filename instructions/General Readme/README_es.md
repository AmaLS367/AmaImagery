# genai — Guía del proyecto (Español)

## Resumen

Proyecto de generación de imágenes. Componentes principales:
- Backend: FastAPI en Python (puerto 8000).
- Frontend: React + TypeScript + Vite (puerto 5173 en dev).

Esta guía explica cómo ejecutar, el flujo de generación, logs y resolución de problemas.

---

## Inicio rápido

Requisitos: Python 3.11+, Node.js 18+

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
cd frontend
npm install
npm run dev
```

Notas: usar rutas relativas (`/generate`) en front para que Vite proxy redirija al backend.

---

## Flujo de generación

1. Usuario hace click → `Generate.tsx` construye payload.
2. Front encola tarea en `RequestQueue`.
3. `generateJSON` hace POST a `/generate`.
4. Vite proxy redirige a `http://localhost:8000/generate`.
5. Backend procesa y devuelve `{path, prompt_hash}`.
6. Front muestra la imagen desde `/file?path=`.

---

## Depuración rápida

- Si no aparece petición: abrir DevTools Console + Network. Verificar logs del clic.
- Si petición falla por CORS o SSL: revisar `vite.config.ts` y `frontend/.env`.
- Test directo con curl para validar backend.

---

## Notas finales

- Para producción: servir frontend estático, usar Nginx + TLS, proteger `/generate`.
- Puedo ampliar la guía con diagramas o instrucciones de despliegue Docker si lo necesitas.
