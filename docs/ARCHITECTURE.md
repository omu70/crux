# Architecture

## High level

```
┌──────────────┐     /api/* (proxied)     ┌──────────────┐      SQL       ┌────────────┐
│  Next.js 15  │ ───────────────────────▶ │   FastAPI    │ ─────────────▶ │ PostgreSQL │
│  (Vercel)    │ ◀─────────────────────── │ (Render/Rwy) │ ◀───────────── │ (Supabase) │
└──────────────┘        JSON + JWT         └──────────────┘                └────────────┘
        │                                         │
        │ React Query cache                       ├── Gemini (AI insights)
        │ next-themes (dark/light)                ├── Resend (email)
        └── localStorage (JWT)                     ├── Supabase Storage (documents)
                                                   └── Meta / Shopify / Woo / GA4 / GSC
```

## Frontend

- **App Router** with three areas: marketing (`/`, `/login`, `/admin/login`), the client
  portal (`/dashboard/*`) and the admin console (`/admin/*`).
- **`Shell`** provides the sidebar + topbar and a client-side auth guard that redirects
  based on role. Route groups keep client and admin navigation separate.
- **Data layer:** a thin `api()` client attaches the JWT, transparently refreshes on 401,
  and is wrapped by React Query hooks in `lib/hooks.ts`.
- **Design system:** Tailwind with CSS-variable theming (`globals.css`) drives dark/light,
  glassmorphism (`.glass`), the aurora background, and a small shadcn-style UI kit
  (`components/ui.tsx`). Charts are Recharts wrappers that read theme colors via CSS vars.

## Backend

- **Layered FastAPI app:** `core` (config, db, security, deps, rate limiting, audit) →
  `models` (SQLAlchemy) → `schemas` (Pydantic) → `routers` (HTTP) → `services` (AI,
  email, storage, KPI math, integrations).
- **Auth:** bcrypt hashing + PyJWT access/refresh tokens. Dependencies `get_current_user`,
  `require_admin`, and `get_current_client` enforce RBAC and client scoping (a client can
  only ever read its own data; suspended clients are blocked).
- **KPIs:** `services/kpi.py` resolves named date ranges, aggregates daily
  `MetricSnapshot` rows (sum vs average per metric), and computes deltas vs the previous
  comparable period — including "lower is better" handling for CPA/CPM.
- **AI:** `services/ai.py` uses Gemini when `GEMINI_API_KEY` is set, otherwise a
  deterministic rule-based analyzer, so insights always work.

## Data model — Prisma vs SQLAlchemy

`prisma/schema.prisma` is the **canonical** database model and the source for
`migrations/0001_init/migration.sql` (native Postgres enums, UUID defaults). The FastAPI
service ships **SQLAlchemy models that mirror it 1:1** (same table/column names via
snake_case), using portable column types (String ids/enums, JSON) so the exact same code
runs on **PostgreSQL** (production) and **SQLite** (zero-config dev/tests).

- **Production:** apply the Prisma SQL migration to Supabase, point `DATABASE_URL` at it.
- **Dev/tests:** leave `DATABASE_URL` blank → SQLite file; `init_db()` creates tables via
  `create_all`. Uniqueness and relationships match the canonical schema; email uniqueness
  is additionally enforced in application code on client creation.

## Request lifecycle

1. Browser calls `/api/...` → Next rewrite proxies to FastAPI.
2. `RateLimitMiddleware` checks the per-IP/route window.
3. Route dependency validates the JWT and resolves the user/client.
4. Handler queries via SQLAlchemy, returns Pydantic-validated JSON.
5. Sensitive actions append an `AuditLog` row.

## Extending

- **New KPI:** add the column to the Prisma schema + SQL migration + SQLAlchemy model,
  then to `KPI_DEFS` in `services/kpi.py` — it appears on the dashboard automatically.
- **New integration:** implement a client in `services/integrations/` following the
  `BaseIntegration` surface and register it in `REGISTRY`.
- **New dashboard section:** add a hook in `lib/hooks.ts`, a page under
  `app/dashboard/<section>/`, and a nav entry in `app/dashboard/layout.tsx`.
