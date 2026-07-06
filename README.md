<div align="center">

# CRUX — by DiziGroww

### Where Growth Becomes Crystal Clear.

A premium, enterprise-grade **client portal** where DiziGroww clients log in to monitor
everything about their digital marketing — Meta Ads, orders, revenue, ROAS, website
performance, SEO, growth reports and AI insights — from one beautiful dashboard.

</div>

---

## 🧠 Aether AI — The AI Media Buyer That Never Sleeps

CRUX now ships with **Aether AI**: a full AI media-buying operating system layered on
the portal. Ten AI modules (business intelligence, competitor intelligence, audience
personas, creative generation across 13 frameworks, visual scoring, campaign builder
with Meta publishing, performance analyst, fatigue detection, budget optimizer,
market research), an 11-agent council that debates and votes on strategy, per-client
RAG memory on pgvector, predictive CTR/ROAS models, 8-dimension campaign scoring,
morning-briefing automations on Celery, and Stripe plan gating. Everything runs with
**zero API keys** (deterministic mock mode) and upgrades to OpenAI / Anthropic /
Gemini / Meta / Stripe the moment keys are added. Full docs: [`docs/AETHER.md`](docs/AETHER.md).
Open the dashboard → **Aether AI** section (12 module pages under `/dashboard/aether`).

---

## ✨ Overview

CRUX is a full-stack SaaS application split into a **Next.js 15** frontend and a
**FastAPI** backend backed by **PostgreSQL** (Supabase in production, Docker/SQLite in
development). It ships with secure JWT auth, a rich client dashboard, a full admin
console, seeded demo data, Docker support, tests, and drop-in API-integration clients.

- **Design language:** Stripe Dashboard × Linear × Vercel × Notion × Apple — minimal, fast, premium, dark + light, fully responsive.
- **Runs today:** `docker compose up` (or run each service manually) and log in with the seeded accounts below.
- **Production-ready:** environment-driven config, role-based access, rate limiting, audit logs, error handling.

## 🧱 Tech stack

| Layer | Technology |
|------|------------|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn-style UI, Framer Motion, React Query, Recharts, Lucide |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2, PyJWT, bcrypt |
| Database | PostgreSQL · Prisma schema (canonical) · Supabase in production |
| Auth | Username + password, bcrypt hashing, JWT access/refresh, session handling, RBAC |
| Storage | Supabase Storage (local filesystem fallback in dev) |
| Integrations | Meta Marketing API, Shopify, WooCommerce, GA4, Search Console, Microsoft Clarity, Gemini AI, Resend |

## 📂 Project structure

```
CRUX/
├── prisma/                 # Canonical DB schema + SQL migration
│   ├── schema.prisma
│   └── migrations/0001_init/migration.sql
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── core/           # config, database, security, deps, rate limit, audit
│   │   ├── models/         # SQLAlchemy models (mirror the Prisma schema)
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── routers/        # auth, dashboard, marketing, insights, collab, admin, clients
│   │   ├── services/       # ai (Gemini), email (Resend), storage, kpi, integrations/
│   │   ├── main.py         # app entrypoint
│   │   └── seed.py         # demo data generator
│   ├── tests/              # pytest suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Next.js application
│   └── src/
│       ├── app/            # routes: landing, login, admin/login, dashboard/*, admin/*
│       ├── components/     # ui kit, dashboard widgets, charts, shell
│       ├── lib/            # api client, auth, hooks, providers, utils
│       └── types/
├── docs/                   # DEPLOYMENT, API, ARCHITECTURE, INTEGRATIONS
├── docker-compose.yml
└── .env.example
```

## 🚀 Quickstart

### Option A — Docker (everything at once)

```bash
cp .env.example .env         # then set a strong JWT_SECRET
docker compose up --build
```

- Frontend → http://localhost:3000
- Backend API + docs → http://localhost:8000/docs
- Postgres → localhost:5432 (seeded automatically on first boot)

### Option B — Run services manually

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # DATABASE_URL blank ⇒ instant local SQLite
python -m app.seed           # create demo admin + clients + data
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## 🔑 Demo accounts

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@12345` |
| Client | `lumina` | `Client@12345` |
| Client | `northpeak` | `Client@12345` |

> Change these via the backend `.env` (`SEED_ADMIN_*`) before seeding, and rotate all
> credentials before going live.

## 🗄️ Using your Supabase database

Your project: **`https://kiupgoucjytmuxygblps.supabase.co`**

1. In Supabase → **Settings → Database → Connection string (URI)**, copy the connection string and set it as `DATABASE_URL` in `backend/.env`, changing the scheme to `postgresql+psycopg2://`:
   ```
   DATABASE_URL=postgresql+psycopg2://postgres:YOUR-DB-PASSWORD@db.kiupgoucjytmuxygblps.supabase.co:5432/postgres
   ```
2. Apply the schema:
   ```bash
   psql "postgresql://postgres:YOUR-DB-PASSWORD@db.kiupgoucjytmuxygblps.supabase.co:5432/postgres" \
     -f prisma/migrations/0001_init/migration.sql
   ```
   *(or `cd prisma && DATABASE_URL=... npx prisma migrate deploy`)*
3. (Optional) For file uploads, create a Storage bucket named `crux-documents` and set `SUPABASE_SERVICE_ROLE_KEY`.
4. Seed: `python -m app.seed`.

**Two secrets are still needed from you:** your **database password** (for `DATABASE_URL`) and, if you want Storage uploads, the **service-role key**. Paste them into `backend/.env`.

## 🔌 Integrations

External marketing data is supplied per client — either entered/uploaded by an admin
(Admin → Clients → *client* → *Add daily metrics / Connect integrations*) or pulled
automatically once you drop credentials into `.env`. See **docs/INTEGRATIONS.md** for the
exact API request shapes and code locations for Meta, Shopify, WooCommerce, GA4, Search
Console, Gemini and Resend.

## ✅ Testing

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

The suite covers auth, JWT, RBAC, the client dashboard, marketing endpoints, insights,
collaboration features and the full admin client lifecycle.

## 🔒 Security

Passwords are bcrypt-hashed (12 rounds). Access is JWT-based with short-lived access
tokens + refresh tokens. Every sensitive action is written to an audit log. The API is
rate-limited per client/route, CORS-restricted, and all secrets live in environment
variables. Role-based access separates `ADMIN` and `CLIENT`.

## 📦 Deployment

Frontend → **Vercel**, backend → **Render/Railway**, database + storage → **Supabase**.
Step-by-step guide in **docs/DEPLOYMENT.md**.

---

<div align="center"><sub>Powered by DiziGroww · Built to look like software worth $500/month.</sub></div>
