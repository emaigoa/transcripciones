# Transcripciones Drive

Proyecto separado en:

- `drive_transcriber/` y `transcripciones/`: backend Django + Selenium.
- `frontend-vercel/`: frontend estatico para Vercel.

## Backend

La API principal es:

```http
POST /api/transcripciones/
Content-Type: application/json

{
  "url": "https://drive.google.com/..."
}
```

Respuesta:

```json
{
  "title": "Clase 6",
  "transcript": "texto...",
  "segment_count": 120
}
```

Health check:

```text
GET /api/health/
```

## Variables de entorno del backend

```text
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=transcripciones.fly.dev
DJANGO_CORS_ALLOWED_ORIGINS=https://tu-front.vercel.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-front.vercel.app
```

## Deploy del backend

Este backend necesita Docker porque usa Selenium + Chromium. Puedes usar Fly.io, Render, Railway u otro proveedor que acepte Docker.

Si Fly no funciona en tu PC, puedes usar Render:

1. Sube este repo a GitHub.
2. En Render, crea un **Blueprint** usando `render.yaml`, o crea un **Web Service** con Docker.
3. Configura las variables de entorno del backend.
4. Deploy.

## Frontend en Vercel

En Vercel:

1. Crea un proyecto nuevo.
2. Usa este repo.
3. En **Root Directory**, selecciona:

```text
frontend-vercel
```

4. No configures build command.
5. Si tu API no esta en `https://transcripciones.fly.dev`, edita:

```text
frontend-vercel/config.js
```

## Desarrollo local

Backend:

```powershell
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

Frontend:

Abre `frontend-vercel/index.html` o subelo a Vercel.
