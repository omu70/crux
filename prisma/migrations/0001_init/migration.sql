-- ============================================================================
-- CRUX by DiziGroww — initial schema (PostgreSQL / Supabase)
-- Apply with: psql "$DATABASE_URL" -f prisma/migrations/0001_init/migration.sql
-- or via `npx prisma migrate deploy`
-- ============================================================================

-- Enums -----------------------------------------------------------------------
CREATE TYPE "Role" AS ENUM ('ADMIN', 'CLIENT');
CREATE TYPE "ClientStatus" AS ENUM ('ACTIVE', 'SUSPENDED');
CREATE TYPE "IntegrationType" AS ENUM ('META_ADS', 'SHOPIFY', 'WOOCOMMERCE', 'GA4', 'SEARCH_CONSOLE', 'CLARITY', 'WEBSITE');
CREATE TYPE "IntegrationStatus" AS ENUM ('CONNECTED', 'DISCONNECTED', 'ERROR', 'PENDING');
CREATE TYPE "CampaignStatus" AS ENUM ('ACTIVE', 'PAUSED', 'REJECTED', 'LEARNING');
CREATE TYPE "OrderStatus" AS ENUM ('PAID', 'CANCELLED', 'REFUNDED', 'PENDING');
CREATE TYPE "TaskStatus" AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED');
CREATE TYPE "Priority" AS ENUM ('LOW', 'MEDIUM', 'HIGH');
CREATE TYPE "GoalType" AS ENUM ('REVENUE', 'ROAS', 'LEADS', 'SALES');
CREATE TYPE "DocumentCategory" AS ENUM ('INVOICE', 'REPORT', 'CREATIVE', 'CONTRACT', 'OTHER');
CREATE TYPE "TicketStatus" AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED');
CREATE TYPE "NotificationType" AS ENUM ('CAMPAIGN_APPROVED', 'CAMPAIGN_REJECTED', 'CREATIVE_UPLOADED', 'BUDGET_INCREASED', 'MEETING_SCHEDULED', 'REPORT_READY', 'GENERAL');
CREATE TYPE "AlertType" AS ENUM ('CPA_INCREASE', 'ROAS_DROP', 'REVENUE_DROP', 'WEBSITE_DOWN', 'PIXEL_DISCONNECTED', 'GA_DISCONNECTED', 'SHOPIFY_DISCONNECTED');
CREATE TYPE "AlertSeverity" AS ENUM ('INFO', 'WARNING', 'CRITICAL');

-- Identity --------------------------------------------------------------------
CREATE TABLE "users" (
  "id"            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "email"         TEXT NOT NULL UNIQUE,
  "username"      TEXT NOT NULL UNIQUE,
  "password_hash" TEXT NOT NULL,
  "role"          "Role" NOT NULL DEFAULT 'CLIENT',
  "is_active"     BOOLEAN NOT NULL DEFAULT TRUE,
  "last_login_at" TIMESTAMPTZ,
  "created_at"    TIMESTAMPTZ NOT NULL DEFAULT now(),
  "updated_at"    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE "account_managers" (
  "id"         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "name"       TEXT NOT NULL,
  "email"      TEXT NOT NULL UNIQUE,
  "title"      TEXT NOT NULL DEFAULT 'Account Manager',
  "avatar_url" TEXT,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE "clients" (
  "id"                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "user_id"                UUID NOT NULL UNIQUE REFERENCES "users"("id") ON DELETE CASCADE,
  "company_name"           TEXT NOT NULL,
  "contact_name"           TEXT NOT NULL,
  "plan"                   TEXT NOT NULL DEFAULT 'Growth',
  "status"                 "ClientStatus" NOT NULL DEFAULT 'ACTIVE',
  "currency"               TEXT NOT NULL DEFAULT 'USD',
  "timezone"               TEXT NOT NULL DEFAULT 'UTC',
  "logo_url"               TEXT,
  "monthly_budget"         DOUBLE PRECISION NOT NULL DEFAULT 0,
  "monthly_target_revenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "monthly_target_roas"    DOUBLE PRECISION NOT NULL DEFAULT 0,
  "monthly_target_leads"   INTEGER NOT NULL DEFAULT 0,
  "account_manager_id"     UUID REFERENCES "account_managers"("id"),
  "created_at"             TIMESTAMPTZ NOT NULL DEFAULT now(),
  "updated_at"             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Integrations ----------------------------------------------------------------
CREATE TABLE "integrations" (
  "id"             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"      UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "type"           "IntegrationType" NOT NULL,
  "status"         "IntegrationStatus" NOT NULL DEFAULT 'PENDING',
  "external_id"    TEXT,
  "account_name"   TEXT,
  "config"         JSONB,
  "last_synced_at" TIMESTAMPTZ,
  "created_at"     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE ("client_id", "type")
);

-- Metrics ---------------------------------------------------------------------
CREATE TABLE "metric_snapshots" (
  "id"                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"           UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "date"                DATE NOT NULL,
  "revenue"             DOUBLE PRECISION NOT NULL DEFAULT 0,
  "orders"              INTEGER NOT NULL DEFAULT 0,
  "ad_spend"            DOUBLE PRECISION NOT NULL DEFAULT 0,
  "roas"                DOUBLE PRECISION NOT NULL DEFAULT 0,
  "ctr"                 DOUBLE PRECISION NOT NULL DEFAULT 0,
  "cpa"                 DOUBLE PRECISION NOT NULL DEFAULT 0,
  "cpm"                 DOUBLE PRECISION NOT NULL DEFAULT 0,
  "conversion_rate"     DOUBLE PRECISION NOT NULL DEFAULT 0,
  "aov"                 DOUBLE PRECISION NOT NULL DEFAULT 0,
  "revenue_growth"      DOUBLE PRECISION NOT NULL DEFAULT 0,
  "sessions"            INTEGER NOT NULL DEFAULT 0,
  "returning_customers" INTEGER NOT NULL DEFAULT 0,
  "new_customers"       INTEGER NOT NULL DEFAULT 0,
  "profit_estimate"     DOUBLE PRECISION NOT NULL DEFAULT 0,
  "lead_count"          INTEGER NOT NULL DEFAULT 0,
  "whatsapp_leads"      INTEGER NOT NULL DEFAULT 0,
  "phone_calls"         INTEGER NOT NULL DEFAULT 0,
  "impressions"         INTEGER NOT NULL DEFAULT 0,
  "clicks"              INTEGER NOT NULL DEFAULT 0,
  "reach"               INTEGER NOT NULL DEFAULT 0,
  UNIQUE ("client_id", "date")
);
CREATE INDEX "idx_metric_client_date" ON "metric_snapshots" ("client_id", "date");

CREATE TABLE "campaigns" (
  "id"            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"     UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "external_id"   TEXT,
  "name"          TEXT NOT NULL,
  "status"        "CampaignStatus" NOT NULL DEFAULT 'ACTIVE',
  "objective"     TEXT NOT NULL DEFAULT 'CONVERSIONS',
  "spend"         DOUBLE PRECISION NOT NULL DEFAULT 0,
  "reach"         INTEGER NOT NULL DEFAULT 0,
  "frequency"     DOUBLE PRECISION NOT NULL DEFAULT 0,
  "ctr"           DOUBLE PRECISION NOT NULL DEFAULT 0,
  "clicks"        INTEGER NOT NULL DEFAULT 0,
  "impressions"   INTEGER NOT NULL DEFAULT 0,
  "cpm"           DOUBLE PRECISION NOT NULL DEFAULT 0,
  "cpa"           DOUBLE PRECISION NOT NULL DEFAULT 0,
  "conversions"   INTEGER NOT NULL DEFAULT 0,
  "purchase_roas" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "revenue"       DOUBLE PRECISION NOT NULL DEFAULT 0,
  "is_winning"    BOOLEAN NOT NULL DEFAULT FALSE,
  "is_losing"     BOOLEAN NOT NULL DEFAULT FALSE,
  "updated_at"    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_campaign_client" ON "campaigns" ("client_id");

CREATE TABLE "orders" (
  "id"            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"     UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "external_id"   TEXT,
  "order_number"  TEXT NOT NULL,
  "customer_name" TEXT NOT NULL,
  "total"         DOUBLE PRECISION NOT NULL DEFAULT 0,
  "status"        "OrderStatus" NOT NULL DEFAULT 'PAID',
  "items_count"   INTEGER NOT NULL DEFAULT 1,
  "source"        TEXT NOT NULL DEFAULT 'shopify',
  "created_at"    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_order_client_created" ON "orders" ("client_id", "created_at");

CREATE TABLE "products" (
  "id"          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"   UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "external_id" TEXT,
  "title"       TEXT NOT NULL,
  "category"    TEXT NOT NULL DEFAULT 'General',
  "price"       DOUBLE PRECISION NOT NULL DEFAULT 0,
  "units_sold"  INTEGER NOT NULL DEFAULT 0,
  "revenue"     DOUBLE PRECISION NOT NULL DEFAULT 0,
  "inventory"   INTEGER NOT NULL DEFAULT 0,
  "low_stock"   BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX "idx_product_client" ON "products" ("client_id");

CREATE TABLE "analytics_snapshots" (
  "id"              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"       UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "date"            DATE NOT NULL,
  "visitors"        INTEGER NOT NULL DEFAULT 0,
  "sessions"        INTEGER NOT NULL DEFAULT 0,
  "bounce_rate"     DOUBLE PRECISION NOT NULL DEFAULT 0,
  "engagement_time" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "organic"         INTEGER NOT NULL DEFAULT 0,
  "paid"            INTEGER NOT NULL DEFAULT 0,
  "direct"          INTEGER NOT NULL DEFAULT 0,
  "referral"        INTEGER NOT NULL DEFAULT 0,
  "top_countries"   JSONB,
  "top_cities"      JSONB,
  "devices"         JSONB,
  "browsers"        JSONB,
  UNIQUE ("client_id", "date")
);

CREATE TABLE "search_console_snapshots" (
  "id"           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"    UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "date"         DATE NOT NULL,
  "clicks"       INTEGER NOT NULL DEFAULT 0,
  "impressions"  INTEGER NOT NULL DEFAULT 0,
  "avg_position" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "ctr"          DOUBLE PRECISION NOT NULL DEFAULT 0,
  "top_keywords" JSONB,
  "top_pages"    JSONB,
  UNIQUE ("client_id", "date")
);

CREATE TABLE "seo_snapshots" (
  "id"               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"        UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "date"             DATE NOT NULL,
  "keyword_growth"   DOUBLE PRECISION NOT NULL DEFAULT 0,
  "backlinks"        INTEGER NOT NULL DEFAULT 0,
  "indexed_pages"    INTEGER NOT NULL DEFAULT 0,
  "technical_issues" INTEGER NOT NULL DEFAULT 0,
  "suggestions"      JSONB,
  UNIQUE ("client_id", "date")
);

-- Deliverables ----------------------------------------------------------------
CREATE TABLE "reports" (
  "id"          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"   UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "title"       TEXT NOT NULL,
  "month"       TEXT NOT NULL,
  "summary"     TEXT NOT NULL,
  "wins"        JSONB,
  "losses"      JSONB,
  "kpis"        JSONB,
  "suggestions" JSONB,
  "strategy"    TEXT,
  "file_url"    TEXT,
  "created_by"  TEXT,
  "created_at"  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_report_client" ON "reports" ("client_id");

CREATE TABLE "tasks" (
  "id"              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"       UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "title"           TEXT NOT NULL,
  "description"     TEXT,
  "status"          "TaskStatus" NOT NULL DEFAULT 'PENDING',
  "priority"        "Priority" NOT NULL DEFAULT 'MEDIUM',
  "due_date"        TIMESTAMPTZ,
  "responsible"     TEXT,
  "expected_result" TEXT,
  "timeframe"       TEXT NOT NULL DEFAULT 'week',
  "created_at"      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_task_client_status" ON "tasks" ("client_id", "status");

CREATE TABLE "goals" (
  "id"         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"  UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "type"       "GoalType" NOT NULL,
  "label"      TEXT NOT NULL,
  "target"     DOUBLE PRECISION NOT NULL,
  "current"    DOUBLE PRECISION NOT NULL DEFAULT 0,
  "unit"       TEXT NOT NULL DEFAULT '',
  "period"     TEXT NOT NULL DEFAULT 'month',
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_goal_client" ON "goals" ("client_id");

CREATE TABLE "meeting_notes" (
  "id"            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"     UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "title"         TEXT NOT NULL,
  "notes"         TEXT NOT NULL,
  "action_items"  JSONB,
  "recording_url" TEXT,
  "meeting_date"  TIMESTAMPTZ NOT NULL,
  "created_at"    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_meeting_client" ON "meeting_notes" ("client_id");

CREATE TABLE "notifications" (
  "id"         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"  UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "type"       "NotificationType" NOT NULL DEFAULT 'GENERAL',
  "title"      TEXT NOT NULL,
  "message"    TEXT NOT NULL,
  "read"       BOOLEAN NOT NULL DEFAULT FALSE,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_notification_client_read" ON "notifications" ("client_id", "read");

CREATE TABLE "announcements" (
  "id"         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "title"      TEXT NOT NULL,
  "message"    TEXT NOT NULL,
  "created_by" TEXT,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE "documents" (
  "id"          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"   UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "name"        TEXT NOT NULL,
  "category"    "DocumentCategory" NOT NULL DEFAULT 'OTHER',
  "file_type"   TEXT NOT NULL,
  "file_url"    TEXT NOT NULL,
  "size_bytes"  INTEGER NOT NULL DEFAULT 0,
  "uploaded_by" TEXT,
  "created_at"  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_document_client_category" ON "documents" ("client_id", "category");

CREATE TABLE "tickets" (
  "id"          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"   UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "subject"     TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "priority"    "Priority" NOT NULL DEFAULT 'MEDIUM',
  "status"      "TicketStatus" NOT NULL DEFAULT 'OPEN',
  "created_at"  TIMESTAMPTZ NOT NULL DEFAULT now(),
  "updated_at"  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_ticket_client_status" ON "tickets" ("client_id", "status");

CREATE TABLE "ticket_messages" (
  "id"         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "ticket_id"  UUID NOT NULL REFERENCES "tickets"("id") ON DELETE CASCADE,
  "sender_id"  UUID NOT NULL REFERENCES "users"("id"),
  "body"       TEXT NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_ticketmsg_ticket" ON "ticket_messages" ("ticket_id");

CREATE TABLE "chat_messages" (
  "id"          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"   UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "sender_id"   UUID NOT NULL REFERENCES "users"("id"),
  "sender_role" "Role" NOT NULL,
  "body"        TEXT NOT NULL,
  "read_at"     TIMESTAMPTZ,
  "created_at"  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_chat_client_created" ON "chat_messages" ("client_id", "created_at");

CREATE TABLE "alerts" (
  "id"         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"  UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "type"       "AlertType" NOT NULL,
  "severity"   "AlertSeverity" NOT NULL DEFAULT 'WARNING',
  "title"      TEXT NOT NULL,
  "message"    TEXT NOT NULL,
  "resolved"   BOOLEAN NOT NULL DEFAULT FALSE,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_alert_client_resolved" ON "alerts" ("client_id", "resolved");

CREATE TABLE "ai_insights" (
  "id"         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"  UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "title"      TEXT NOT NULL,
  "body"       TEXT NOT NULL,
  "category"   TEXT NOT NULL DEFAULT 'performance',
  "impact"     "Priority" NOT NULL DEFAULT 'MEDIUM',
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_insight_client" ON "ai_insights" ("client_id");

CREATE TABLE "performance_scores" (
  "id"               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"        UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "date"             DATE NOT NULL,
  "overall"          INTEGER NOT NULL DEFAULT 0,
  "ads_score"        INTEGER NOT NULL DEFAULT 0,
  "seo_score"        INTEGER NOT NULL DEFAULT 0,
  "website_score"    INTEGER NOT NULL DEFAULT 0,
  "revenue_score"    INTEGER NOT NULL DEFAULT 0,
  "speed_score"      INTEGER NOT NULL DEFAULT 0,
  "conversion_score" INTEGER NOT NULL DEFAULT 0,
  UNIQUE ("client_id", "date")
);

CREATE TABLE "website_health" (
  "id"             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "client_id"      UUID NOT NULL REFERENCES "clients"("id") ON DELETE CASCADE,
  "date"           DATE NOT NULL,
  "performance"    INTEGER NOT NULL DEFAULT 0,
  "accessibility"  INTEGER NOT NULL DEFAULT 0,
  "seo"            INTEGER NOT NULL DEFAULT 0,
  "best_practices" INTEGER NOT NULL DEFAULT 0,
  "lcp"            DOUBLE PRECISION NOT NULL DEFAULT 0,
  "fid"            DOUBLE PRECISION NOT NULL DEFAULT 0,
  "cls"            DOUBLE PRECISION NOT NULL DEFAULT 0,
  UNIQUE ("client_id", "date")
);

CREATE TABLE "audit_logs" (
  "id"         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "user_id"    UUID REFERENCES "users"("id"),
  "action"     TEXT NOT NULL,
  "entity"     TEXT,
  "entity_id"  TEXT,
  "ip"         TEXT,
  "meta"       JSONB,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "idx_audit_user" ON "audit_logs" ("user_id");
