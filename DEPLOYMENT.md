# DEPLOYMENT.md

Deployment guide for the DSAT Prep platform: FastAPI backend on a VPS, Supabase for the database, and the React apps on a static hosting provider.

---

## Architecture Overview

```
Static Host (Netlify / Vercel / Cloudflare Pages)
  ├── Student App   (APP/STUDENT_APP_REDUX/dist/)
  └── Admin App     (APP/ADMIN_DASHBOARD/dist/)
           │
           │  HTTPS API calls to VITE_API_BASE
           ▼
VPS (Docker or bare metal)
  └── FastAPI backend  (:8000 or behind nginx)
           │
           │  asyncpg / SQLAlchemy
           ▼
Supabase
  └── PostgreSQL database
```

The student app and admin app are fully static after `npm run build`. They call the FastAPI backend via an environment variable (`VITE_API_BASE`). The backend connects to Supabase using a standard Postgres connection string — no Supabase SDK required.

---

## Before You Deploy — Required Code Change

The frontend API client currently uses a relative base path (`/api`), which works when both apps are on the same domain. For separate deployments you must point it at the VPS.

**`APP/STUDENT_APP_REDUX/src/api/client.ts`** — change line 3:

```ts
// Before
const API_BASE = '/api'

// After
const API_BASE = (import.meta as any).env.VITE_API_BASE || '/api'
```

Apply the same change to the admin app's API client. Then set `VITE_API_BASE` as a build-time environment variable on your hosting provider (see step 2 below).

---

## Step 1 — Supabase (Database)

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Go to **Settings → Database → Connection string** and copy the **URI** (not the pooler URI)
3. It will look like: `postgresql://postgres.[ref]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres`
4. For `asyncpg` (what FastAPI uses) change the scheme: `postgresql+asyncpg://...`
5. Run migrations against the new database (see Step 3)

---

## Step 2 — Static Frontend (Netlify / Vercel / Cloudflare Pages)

### Student App

Build command: `npm run build`  
Publish directory: `dist`  
Root directory: `APP/STUDENT_APP_REDUX`

**Environment variables to set on the hosting provider:**

| Variable | Value |
|---|---|
| `VITE_API_BASE` | `https://your-vps-domain.com/api` |
| `VITE_TEST_USER_TOKEN` | Student auth token (remove once real auth is wired) |

### Admin App

Same process, different root directory (`APP/ADMIN_DASHBOARD` or wherever the admin build lives).

**Environment variables:**

| Variable | Value |
|---|---|
| `VITE_API_BASE` | `https://your-vps-domain.com/api` |

### SPA routing

Both apps use React Router. Add a redirect rule so all paths return `index.html`:

**Netlify** — create `APP/STUDENT_APP_REDUX/public/_redirects`:
```
/*  /index.html  200
```

**Vercel** — create `APP/STUDENT_APP_REDUX/vercel.json`:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

**Cloudflare Pages** — create `APP/STUDENT_APP_REDUX/public/_redirects` (same as Netlify).

---

## Step 3 — VPS (FastAPI Backend)

### Requirements

- Python 3.11+
- `uv` for dependency management
- A process manager (systemd, supervisor, or Docker)
- Optional: nginx as a reverse proxy in front of uvicorn

### Environment variables

Create a `.env` file on the VPS (never commit this):

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Auth
ADMIN_API_KEYS=your-strong-admin-key-here
STUDENT_API_KEYS=your-strong-student-key-here
JWT_SECRET_KEY=your-long-random-secret-here

# CORS — comma-separated list of your frontend domains
CORS_ALLOWED_ORIGINS=https://your-student-app.netlify.app,https://your-admin-app.netlify.app

# LLM providers (only set what you use)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434   # if running Ollama on the same VPS

# Storage (local filesystem by default; configure S3/R2 for production)
OBJECT_STORAGE_BACKEND=local_fs
OBJECT_STORAGE_LOCAL_ROOT=/var/dsat/objects
```

### Run migrations

```bash
cd backend
uv run alembic upgrade head
```

### Start the server

**Development / quick test:**
```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Production (with auto-restart):**
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### nginx reverse proxy (recommended)

```nginx
server {
    listen 80;
    server_name your-vps-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-vps-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-vps-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-vps-domain.com/privkey.pem;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Get a free TLS cert with: `certbot --nginx -d your-vps-domain.com`

---

## Step 4 — Verify the Deploy

```bash
# Backend health check
curl https://your-vps-domain.com/api/health

# Questions endpoint (student key)
curl -H "X-API-Key: your-student-key" https://your-vps-domain.com/api/questions

# Stats endpoint
curl -H "X-API-Key: your-student-key" https://your-vps-domain.com/api/stats/1
```

Open the student app URL in a browser and confirm the dashboard loads without CORS errors (check the browser console).

---

## What Is Deferred Until Online DB Migration

- **User authentication** — currently uses `VITE_TEST_USER_TOKEN` as a hardcoded bearer token. Real login (JWT or Supabase Auth) is wired in after migration.
- **Token-level authorization tests** — backend tests currently skip per-user auth; these will be added once auth is live.
- **Object storage** — ingestion pipeline stores PDFs and crops locally. For a cloud VPS, migrate `OBJECT_STORAGE_BACKEND` to S3 or Cloudflare R2 and configure bucket credentials.

---

## Quick Reference

| Thing | Command |
|---|---|
| Build student app | `cd APP/STUDENT_APP_REDUX && npm run build` |
| Build admin app | `cd APP/ADMIN_DASHBOARD && npm run build` |
| Run migrations | `cd backend && uv run alembic upgrade head` |
| Start backend | `cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Run backend tests | `cd backend && python -m pytest` |
| Run frontend tests | `cd APP/STUDENT_APP_REDUX && npm test -- --run` |
