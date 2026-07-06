-- ============================================================================
-- Aether AI — migration 0002
-- Adds the AI media-buying platform tables + pgvector semantic search.
-- Apply after 0001_init:  psql $DATABASE_URL -f migration.sql
-- All ids/FKs are UUID to match 0001_init. Idempotent (IF NOT EXISTS).
-- ============================================================================

-- pgvector (available on Supabase; safe no-op if already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Module 1: Business Intelligence ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS business_profiles (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id        UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  website_url      TEXT,
  inputs           JSONB,
  status           TEXT NOT NULL DEFAULT 'PENDING',
  summary          TEXT,
  usp              TEXT,
  positioning      TEXT,
  brand_voice      TEXT,
  visual_style     TEXT,
  offers           JSONB,
  price_analysis   JSONB,
  strengths        JSONB,
  weaknesses       JSONB,
  customer_journey JSONB,
  sales_funnel     JSONB,
  pain_points      JSONB,
  desires          JSONB,
  ideal_customers  JSONB,
  raw              JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_bizprofile_client ON business_profiles(client_id);

-- ── Module 2: Competitor Intelligence ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS competitor_profiles (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id        UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  name             TEXT NOT NULL,
  website          TEXT,
  discovered_via   TEXT NOT NULL DEFAULT 'ai',
  threat_level     TEXT NOT NULL DEFAULT 'MEDIUM',
  pricing          JSONB,
  offers           JSONB,
  creative_angles  JSONB,
  headlines        JSONB,
  funnels          JSONB,
  reviews_summary  JSONB,
  ads              JSONB,
  seo              JSONB,
  content_strategy JSONB,
  email_funnels    JSONB,
  swot             JSONB,
  positioning_gap  TEXT,
  last_analyzed_at TIMESTAMPTZ,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_competitor_client ON competitor_profiles(client_id);

-- ── Module 3: Audience Intelligence ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS personas (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id          UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  name               TEXT NOT NULL,
  segment            TEXT,
  awareness_level    TEXT NOT NULL DEFAULT 'problem_aware',
  sophistication     INTEGER NOT NULL DEFAULT 3,
  purchase_intent    TEXT NOT NULL DEFAULT 'MEDIUM',
  pains              JSONB,
  fears              JSONB,
  dream_outcome      JSONB,
  objections         JSONB,
  buying_triggers    JSONB,
  identity           JSONB,
  lifestyle          JSONB,
  language           JSONB,
  behavior           JSONB,
  jobs_to_be_done    JSONB,
  emotional_triggers JSONB,
  targeting          JSONB,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_persona_client ON personas(client_id);

-- ── Module 10 + RAG ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS research_jobs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  query             TEXT NOT NULL,
  sources           JSONB NOT NULL,
  status            TEXT NOT NULL DEFAULT 'PENDING',
  results           JSONB,
  summary           TEXT,
  insights          JSONB,
  voice_of_customer JSONB,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at       TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_research_client ON research_jobs(client_id);

CREATE TABLE IF NOT EXISTS knowledge_documents (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  namespace   TEXT NOT NULL DEFAULT 'general',
  title       TEXT NOT NULL,
  source_type TEXT NOT NULL DEFAULT 'text',
  source_url  TEXT,
  content     TEXT NOT NULL,
  meta        JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_knowdoc_client_ns ON knowledge_documents(client_id, namespace);

CREATE TABLE IF NOT EXISTS embedding_chunks (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id   UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  client_id     UUID NOT NULL,
  namespace     TEXT NOT NULL DEFAULT 'general',
  chunk_index   INTEGER NOT NULL DEFAULT 0,
  content       TEXT NOT NULL,
  token_count   INTEGER NOT NULL DEFAULT 0,
  embedding     JSONB,                 -- portable copy (SQLite parity)
  embedding_vec vector(1024),          -- pgvector column used for ANN search
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chunk_client_ns ON embedding_chunks(client_id, namespace);
-- HNSW index for fast cosine search (Supabase supports hnsw on pgvector >= 0.5)
CREATE INDEX IF NOT EXISTS idx_chunk_vec ON embedding_chunks
  USING hnsw (embedding_vec vector_cosine_ops);

-- ── Modules 4 & 5: Creative + Visual ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS creative_assets (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  persona_id      UUID REFERENCES personas(id) ON DELETE SET NULL,
  batch_id        UUID,
  kind            TEXT NOT NULL,
  framework       TEXT NOT NULL DEFAULT 'AIDA',
  content         TEXT NOT NULL,
  meta            JSONB,
  predicted_score DOUBLE PRECISION NOT NULL DEFAULT 0,
  status          TEXT NOT NULL DEFAULT 'DRAFT',
  performance     JSONB,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_creative_client_kind ON creative_assets(client_id, kind);

CREATE TABLE IF NOT EXISTS visual_analyses (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  asset_url         TEXT NOT NULL,
  kind              TEXT NOT NULL DEFAULT 'image',
  creative_score    INTEGER NOT NULL DEFAULT 0,
  attention_score   INTEGER NOT NULL DEFAULT 0,
  scroll_stop_score INTEGER NOT NULL DEFAULT 0,
  brand_score       INTEGER NOT NULL DEFAULT 0,
  emotion_score     INTEGER NOT NULL DEFAULT 0,
  ctr_prediction    DOUBLE PRECISION NOT NULL DEFAULT 0,
  recommendations   JSONB,
  raw               JSONB,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_visual_client ON visual_analyses(client_id);

-- ── Module 6: Campaign Builder ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS campaign_blueprints (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  name              TEXT NOT NULL,
  objective         TEXT NOT NULL DEFAULT 'OUTCOME_SALES',
  status            TEXT NOT NULL DEFAULT 'DRAFT',
  daily_budget      DOUBLE PRECISION NOT NULL DEFAULT 0,
  structure         JSONB,
  naming            JSONB,
  budget_plan       JSONB,
  audience_strategy JSONB,
  placements        JSONB,
  pixel_mapping     JSONB,
  creative_rotation JSONB,
  scaling_plan      JSONB,
  published_ids     JSONB,
  rationale         TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_blueprint_client ON campaign_blueprints(client_id);

-- ── Multi-agent orchestration ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_runs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'PENDING',
  input       JSONB,
  steps       JSONB,
  messages    JSONB,
  votes       JSONB,
  decision    JSONB,
  error       TEXT,
  tokens_in   INTEGER NOT NULL DEFAULT 0,
  tokens_out  INTEGER NOT NULL DEFAULT 0,
  cost_usd    DOUBLE PRECISION NOT NULL DEFAULT 0,
  started_at  TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agentrun_client_kind ON agent_runs(client_id, kind);

CREATE TABLE IF NOT EXISTS usage_ledger (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id  UUID,
  date       DATE NOT NULL,
  provider   TEXT NOT NULL,
  model      TEXT NOT NULL,
  tokens_in  INTEGER NOT NULL DEFAULT 0,
  tokens_out INTEGER NOT NULL DEFAULT 0,
  cost_usd   DOUBLE PRECISION NOT NULL DEFAULT 0,
  kind       TEXT NOT NULL DEFAULT 'llm'
);
CREATE INDEX IF NOT EXISTS idx_usage_client_date ON usage_ledger(client_id, date);

-- ── Predictive AI + scoring ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id        UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  entity_type      TEXT NOT NULL,
  entity_id        UUID NOT NULL,
  ctr              DOUBLE PRECISION NOT NULL DEFAULT 0,
  cvr              DOUBLE PRECISION NOT NULL DEFAULT 0,
  cpa              DOUBLE PRECISION NOT NULL DEFAULT 0,
  roas             DOUBLE PRECISION NOT NULL DEFAULT 0,
  creative_quality DOUBLE PRECISION NOT NULL DEFAULT 0,
  win_probability  DOUBLE PRECISION NOT NULL DEFAULT 0,
  audience_match   DOUBLE PRECISION NOT NULL DEFAULT 0,
  features         JSONB,
  model_version    TEXT NOT NULL DEFAULT 'heuristic-v1',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_prediction_entity ON predictions(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS campaign_scores (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id    UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  campaign_id  UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  blueprint_id UUID REFERENCES campaign_blueprints(id) ON DELETE CASCADE,
  date         DATE NOT NULL,
  overall      INTEGER NOT NULL DEFAULT 0,
  creative     INTEGER NOT NULL DEFAULT 0,
  audience     INTEGER NOT NULL DEFAULT 0,
  offer        INTEGER NOT NULL DEFAULT 0,
  landing_page INTEGER NOT NULL DEFAULT 0,
  tracking     INTEGER NOT NULL DEFAULT 0,
  brand        INTEGER NOT NULL DEFAULT 0,
  scaling      INTEGER NOT NULL DEFAULT 0,
  details      JSONB
);
CREATE INDEX IF NOT EXISTS idx_campscore_client ON campaign_scores(client_id);

-- ── Modules 8 & 9: Optimization ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fatigue_signals (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id      UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  entity_type    TEXT NOT NULL,
  entity_ref     TEXT NOT NULL,
  fatigue_type   TEXT NOT NULL,
  severity       TEXT NOT NULL DEFAULT 'WARNING',
  evidence       JSONB,
  recommendation TEXT,
  resolved       BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_fatigue_client_resolved ON fatigue_signals(client_id, resolved);

CREATE TABLE IF NOT EXISTS optimization_actions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  campaign_id     UUID REFERENCES campaigns(id) ON DELETE SET NULL,
  campaign_ref    TEXT NOT NULL,
  action          TEXT NOT NULL,
  amount          JSONB,
  reason          TEXT NOT NULL,
  confidence      DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  expected_impact TEXT,
  status          TEXT NOT NULL DEFAULT 'PROPOSED',
  applied_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_optaction_client_status ON optimization_actions(client_id, status);

-- ── Automations + billing ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS automation_runs (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id  UUID REFERENCES clients(id) ON DELETE CASCADE,
  kind       TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'DONE',
  output     JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_automation_kind ON automation_runs(kind, created_at);

CREATE TABLE IF NOT EXISTS subscriptions (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id              UUID NOT NULL UNIQUE REFERENCES clients(id) ON DELETE CASCADE,
  stripe_customer_id     TEXT,
  stripe_subscription_id TEXT,
  plan                   TEXT NOT NULL DEFAULT 'STARTER',
  status                 TEXT NOT NULL DEFAULT 'TRIALING',
  current_period_end     TIMESTAMPTZ,
  meta                   JSONB,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);
