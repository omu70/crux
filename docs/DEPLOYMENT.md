# Deployment Guide

CRUX deploys as three pieces: **frontend → Vercel**, **backend → Render/Railway**,
**database + storage → Supabase**.

## 1. Database — Supabase

1. Create (or use) your project: `kiupgoucjytmuxygblps`.
2. Apply the schema — either:
   - `psql "$DATABASE_URL" -f prisma/migrations/0001_init/migration.sql`, or
   - `cd prisma && DATABASE_URL=... npx prisma migrate deploy`
3. Grab the **URI** connection string from *Settings → Database*. Use the pooled
   connection (port `6543`) for serverless backends, or the direct one (`5432`) for a
   long-running server.
4. (Optional) Create a Storage bucket `crux-documents` (public) for document uploads.

## 2. Backend — Render or Railway

**Render (Docker)**
- New → **Web Service** → point at the repo, root `backend/`.
- Render auto-detects the `Dockerfile`. Start command is baked in.
- Environment variables:
  ```
  DATABASE_URL=postgresql+psycopg2://postgres:PASSWORD@db.<ref>.supabase.co:5432/postgres
  JWT_SECRET=<48+ char random string>
  CORS_ORIGINS=https://your-frontend.vercel.app
  GEMINI_API_KEY=...          # optional
  RESEND_API_KEY=...          # optional
  SUPABASE_URL=https://<ref>.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=... # optional (Storage)
  ```
- After first deploy, run the seed once from the Render shell: `python -m app.seed`
  (or skip and create clients from the admin console).

**Railway**
- New Project → Deploy from repo → set the service root to `backend/`.
- Add the same environment variables. Railway builds the Dockerfile automatically.

> Generate a secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

## 3. Frontend — Vercel

1. Import the repo, set **Root Directory** to `frontend/`.
2. Framework preset: **Next.js** (auto).
3. Environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```
4. Deploy. The rewrite in `next.config.mjs` proxies `/api/*` to your backend, so the
   browser only ever talks to your own origin.

## 4. Post-deploy checklist

- [ ] `GET https://backend/api/health` returns `{"status":"healthy"}`
- [ ] Admin login works and the console loads clients
- [ ] A client can log in and the dashboard renders KPIs + charts
- [ ] CORS origin matches the deployed frontend URL exactly
- [ ] `JWT_SECRET` is strong and **not** the default
- [ ] Rotate the seeded demo passwords

## Scaling notes

- The in-memory rate limiter is per-process. Behind multiple workers/instances, back it
  with Redis (swap `RateLimitMiddleware`'s store).
- Use the Supabase **pooled** connection for serverless/many-instance backends.
- Put the backend behind HTTPS (Render/Railway provide this automatically).
