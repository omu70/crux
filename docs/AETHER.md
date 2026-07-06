# Aether AI — The AI Media Buyer That Never Sleeps

Aether AI is the AI media-buying operating system built into CRUX. It thinks like a
team of eleven specialists — planner, market researcher, brand strategist,
direct-response copywriter, creative strategist, data analyst, media buyer,
memory keeper, decision maker, manager and supervisor — and runs the full loop:
understand the business → research the market → build audiences → generate
creatives → build and launch campaigns → monitor → optimize, every day,
automatically.

## Architecture

```
frontend/src/app/dashboard/aether/*      Next.js module UIs (12 pages)
frontend/src/lib/aether.ts               typed API client + React Query hooks
backend/app/routers/aether.py            44 endpoints under /api/aether
backend/app/modules/                     the 10 AI modules
├── business_intel.py                    M1  business profile from any source
├── competitor_intel.py                  M2  discovery + full competitor profiles
├── audience_intel.py                    M3  deep personas (Schwartz-aware)
├── creative_intel.py                    M4  bulk creative generation, 13 frameworks
├── visual_ai.py                         M5  image/video scoring via vision models
├── campaign_builder.py                  M6  blueprints → Meta publishing (PAUSED)
├── performance_analyst.py               M7  analyst briefs, binding constraint
├── creative_optimizer.py                M8  fatigue detection + auto-refresh
├── budget_optimizer.py                  M9  scale/kill/duplicate actions
└── research_engine.py                   M10 multi-source market research
backend/app/agents/                      multi-agent council
├── prompts.py                           11 role system prompts
└── orchestrator.py                      plan→propose→debate→vote→decide→review
backend/app/ai/                          AI core
├── providers.py                         OpenAI / Anthropic / Gemini over httpx
├── router.py                            role-routed LLM with fallback chain
├── embeddings.py                        text-embedding-3-large (+ mock)
├── vision.py                            GPT-4o / Gemini vision scoring (+ mock)
└── mock.py                              deterministic mock — zero-key operation
backend/app/rag/                         RAG: chunking, pgvector store, ingestion
backend/app/ml/                          predictive models + 8-dim scoring
├── predictors.py                        heuristic tier + optional sklearn GBM tier
└── scoring.py                           Overall/Creative/Audience/Offer/LP/Tracking/Brand/Scaling
backend/app/tasks/automations.py         Celery beat: morning briefings, scans
backend/app/services/meta_publish.py     Meta Graph API publisher (mock-safe)
backend/app/services/billing.py          Stripe subscriptions + plan gating
```

## Design principles

**Degradation ladder.** Every capability has three tiers: real API → alternate
provider → deterministic mock. The platform is fully operable with zero API
keys (demos, tests, CI); adding keys upgrades quality without code changes.

**LLM routing.** `app/ai/router.py` maps each agent role to an ordered provider
chain (strategy/decision → Claude, bulk copy → GPT-4o, research summarization →
Gemini). Failures fall through the chain with retries; all usage lands in
`usage_ledger` with cost estimates per client.

**The council.** For strategic questions, `run_council` runs a real
multi-agent debate: specialists propose, critique each other by name, concede
points, vote with confidence, the Decision agent synthesizes (decision, why,
risks, kill criteria, first-48h actions) and the Supervisor quality-gates the
result. The full transcript persists on `agent_runs` and is replayable in the
Council UI.

**Memory (RAG).** Everything the system learns — websites, uploads, research,
competitor profiles, its own analyses — is chunked, embedded and stored per
client in namespaces (`business`, `brand`, `research`, `creatives`,
`performance`). On Postgres, search uses pgvector HNSW cosine; on SQLite, the
same API computes cosine in-process. Every module retrieves context before
prompting, so outputs compound in specificity over time.

**Safety rails.** Campaign publishing always creates PAUSED objects; budget
actions are PROPOSED until a human applies them; applied actions record a
rollback condition. The optimizer respects learning phase (no verdicts before
~10 conversions / meaningful spend) and caps vertical scaling at 20-30%/day.

## Automations (Celery beat)

| Schedule | Task | What it does |
|---|---|---|
| daily 08:00 UTC | `morning_briefing_all` | analyst brief + fatigue scan + budget review per client → in-app notification + email |
| 09:30 & 17:30 | `fatigue_scan_all` | creative/audience/offer/ad fatigue signals |
| daily 11:00 | `budget_review_all` | fresh scale/kill/duplicate proposals |
| Mon 03:00 | `retrain_models_all` | retrain per-account GBM predictors (needs sklearn + ≥25 spent campaigns) |

Without `REDIS_URL`, Celery runs eagerly in-process (dev/test); with Redis, run
`celery -A app.worker worker` and `celery -A app.worker beat` (docker-compose
ships both).

## Predictive tiers

`heuristic-v1` (always on): calibrated feature-based scoring — creative quality
from direct-response craft signals, campaign win-probability from
CTR/ROAS/frequency vs benchmarks. `gbm-v1` (optional): per-account
GradientBoosting models for CTR/ROAS/CPA, trained weekly once an account has
≥25 spent campaigns, persisted to `backend/uploads/models/`.

## Billing

Three plans (Starter $99 / Growth $299 / Scale $799) with metered limits on
creatives, councils, research jobs and competitors — enforced with HTTP 402 at
the API. Stripe checkout + webhook when keys exist; instant mock upgrades
without.

## Database

Migration `prisma/migrations/0002_aether/migration.sql` adds 16 tables and the
pgvector extension (docker-compose now uses the `pgvector/pgvector:pg16`
image; Supabase has pgvector built in). SQLAlchemy mirrors live in
`backend/app/models/aether.py`; Prisma models in `prisma/schema.prisma`
(scalar `clientId` references keep legacy CRUX models untouched — FKs are
enforced in SQL).

## Running

```bash
docker compose up            # db(pgvector) + redis + api + worker + beat + frontend
# or dev, zero setup:
cd backend && uvicorn app.main:app --reload     # SQLite + eager Celery + mock AI
cd frontend && npm run dev
```

Set any of `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` to switch
from mock to real intelligence; `META_ACCESS_TOKEN` + `META_AD_ACCOUNT_ID` (+
page/pixel ids) to publish real paused campaigns; `STRIPE_*` for live billing.

## Tests

`backend/tests/test_aether.py` — 16 end-to-end tests covering every module in
deterministic mock mode, including plan-limit gating, publish flow, fatigue →
auto-refresh, and the full council transcript.
