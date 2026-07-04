# API Reference

Base URL: `http://localhost:8000` · Interactive docs: `/docs` (Swagger) · `/redoc`.
All `/api/*` routes except auth require a `Authorization: Bearer <access_token>` header.

## Auth

| Method | Path | Body | Notes |
|--------|------|------|-------|
| POST | `/api/auth/login` | `{username, password, remember?}` | Client or admin login → token pair |
| POST | `/api/auth/admin/login` | `{username, password}` | Rejects non-admins |
| POST | `/api/auth/refresh` | `{refresh_token}` | New token pair |
| GET | `/api/auth/me` | — | Current user |
| POST | `/api/auth/forgot-password` | `{username}` | Always 200 (no enumeration) |

```bash
# Login and capture the token
TOKEN=$(curl -s localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"lumina","password":"Client@12345"}' | jq -r .access_token)

curl localhost:8000/api/dashboard/summary -H "Authorization: Bearer $TOKEN"
```

## Client dashboard

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/dashboard/summary?range=30d` | Greeting, client profile, 17 KPI cards |
| GET | `/api/dashboard/kpis?range=&date_from=&date_to=` | KPI cards for a range |
| GET | `/api/dashboard/timeseries?metrics=revenue,orders&range=30d` | Chart series |
| GET | `/api/dashboard/performance-score` | 0–100 overall + breakdown |
| GET | `/api/dashboard/website-health` | Core Web Vitals + Lighthouse |
| GET | `/api/dashboard/alerts` | Active smart alerts |

Ranges: `today · yesterday · 7d · 30d · last_month · quarter · custom` (with `date_from`/`date_to`).

## Marketing

`GET /api/marketing/{campaigns,ecommerce,analytics,search-console,seo}`

## Insights & reports

`GET /api/insights` · `POST /api/insights/generate` · `GET /api/insights/plan` ·
`GET /api/reports` · `GET /api/reports/{id}`

## Collaboration

`GET/POST /api/tasks`, `PATCH /api/tasks/{id}` · `GET /api/goals` ·
`GET /api/meeting-notes` · `GET /api/notifications`, `POST /api/notifications/{id}/read` ·
`GET /api/documents` · `GET/POST /api/tickets`, `GET /api/tickets/{id}`,
`POST /api/tickets/{id}/reply` · `GET/POST /api/chat`

## Admin (role `ADMIN`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/admin/overview` | Client counts, tracked revenue, activity |
| GET | `/api/admin/api-status` | Which integrations have credentials |
| GET | `/api/admin/audit-logs` | Audit trail |
| GET/POST | `/api/admin/clients` | List / create clients |
| GET/PATCH/DELETE | `/api/admin/clients/{id}` | Read / update / delete |
| PATCH | `/api/admin/clients/{id}/credentials` | Assign username/password |
| PATCH | `/api/admin/clients/{id}/targets` | Assign budget & targets |
| POST | `/api/admin/clients/{id}/suspend` · `/activate` | Toggle status |
| GET/POST | `/api/admin/clients/{id}/integrations` | Connect integrations |
| POST | `/api/admin/clients/{id}/metrics` | Upsert a day's metrics (manual entry) |
| POST | `/api/admin/clients/{id}/documents` | Multipart file upload |
| POST | `/api/admin/clients/{id}/{reports,tasks,goals,meeting-notes,alerts}` | Create content |
| POST | `/api/admin/clients/{id}/switch` | Get a CLIENT token to view their dashboard |
| POST | `/api/admin/{announcements,notifications}` | Broadcast / target |

### Example — create a client

```bash
curl -X POST localhost:8000/api/admin/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H 'Content-Type: application/json' \
  -d '{"company_name":"Acme","contact_name":"Jane","username":"acme",
       "password":"S3curePass!","email":"[email protected]","plan":"Growth",
       "monthly_budget":12000,"monthly_target_revenue":90000,"monthly_target_roas":4}'
```

### Example — enter a day of metrics manually

```bash
curl -X POST localhost:8000/api/admin/clients/$CID/metrics \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H 'Content-Type: application/json' \
  -d '{"date":"2026-07-01","revenue":5230,"orders":42,"ad_spend":1180,"roas":4.43}'
```
