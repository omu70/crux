"""Aether AI — SQLAlchemy models for the AI media-buying platform.

Mirrors the Aether section of prisma/schema.prisma. Portable column types
(String ids, String enums, JSON) so the same models run on PostgreSQL
(Supabase / Docker, where embeddings additionally use pgvector via raw SQL)
and SQLite (dev / tests, where embeddings fall back to JSON + in-process
cosine similarity).
"""
from __future__ import annotations

import datetime as dt
from uuid import uuid4

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, JSON,
    Index, UniqueConstraint,
)
from sqlalchemy.orm import mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid4())


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# Module 1 — Business Intelligence
# ─────────────────────────────────────────────────────────────────────────────
class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    __table_args__ = (Index("idx_bizprofile_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    website_url = mapped_column(String(500), nullable=True)
    inputs = mapped_column(JSON, nullable=True)            # {website, shopify, csv, pdf, socials, catalog...}
    status = mapped_column(String(16), default="PENDING", nullable=False)  # PENDING|ANALYZING|READY|FAILED

    summary = mapped_column(Text, nullable=True)
    usp = mapped_column(Text, nullable=True)
    positioning = mapped_column(Text, nullable=True)
    brand_voice = mapped_column(Text, nullable=True)
    visual_style = mapped_column(Text, nullable=True)
    offers = mapped_column(JSON, nullable=True)            # [{name, price, type, angle}]
    price_analysis = mapped_column(JSON, nullable=True)    # {tier, vs_market, elasticity_notes}
    strengths = mapped_column(JSON, nullable=True)         # [str]
    weaknesses = mapped_column(JSON, nullable=True)        # [str]
    customer_journey = mapped_column(JSON, nullable=True)  # [{stage, touchpoint, friction}]
    sales_funnel = mapped_column(JSON, nullable=True)      # [{step, url, purpose, leak_risk}]
    pain_points = mapped_column(JSON, nullable=True)       # [str]
    desires = mapped_column(JSON, nullable=True)           # [{desire, intensity, evidence}]
    ideal_customers = mapped_column(JSON, nullable=True)   # [short persona seeds]
    raw = mapped_column(JSON, nullable=True)               # full agent output for audit

    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# Module 2 — Competitor Intelligence
# ─────────────────────────────────────────────────────────────────────────────
class CompetitorProfile(Base):
    __tablename__ = "competitor_profiles"
    __table_args__ = (Index("idx_competitor_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = mapped_column(String(200), nullable=False)
    website = mapped_column(String(500), nullable=True)
    discovered_via = mapped_column(String(60), default="ai", nullable=False)  # ai|manual|research
    threat_level = mapped_column(String(10), default="MEDIUM", nullable=False)

    pricing = mapped_column(JSON, nullable=True)
    offers = mapped_column(JSON, nullable=True)
    creative_angles = mapped_column(JSON, nullable=True)
    headlines = mapped_column(JSON, nullable=True)
    funnels = mapped_column(JSON, nullable=True)
    reviews_summary = mapped_column(JSON, nullable=True)   # {positives, negatives, themes}
    ads = mapped_column(JSON, nullable=True)               # {facebook: [], instagram: [], google: []}
    seo = mapped_column(JSON, nullable=True)               # {keywords, authority_estimate}
    content_strategy = mapped_column(JSON, nullable=True)
    email_funnels = mapped_column(JSON, nullable=True)
    swot = mapped_column(JSON, nullable=True)              # {strengths, weaknesses, opportunities, threats}
    positioning_gap = mapped_column(Text, nullable=True)   # how the client can win against this competitor

    last_analyzed_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# Module 3 — Audience Intelligence
# ─────────────────────────────────────────────────────────────────────────────
class Persona(Base):
    __tablename__ = "personas"
    __table_args__ = (Index("idx_persona_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = mapped_column(String(160), nullable=False)          # "Overwhelmed Ops Olivia"
    segment = mapped_column(String(160), nullable=True)
    awareness_level = mapped_column(String(24), default="problem_aware", nullable=False)
    # unaware|problem_aware|solution_aware|product_aware|most_aware
    sophistication = mapped_column(Integer, default=3, nullable=False)   # Schwartz stage 1-5
    purchase_intent = mapped_column(String(10), default="MEDIUM", nullable=False)

    pains = mapped_column(JSON, nullable=True)
    fears = mapped_column(JSON, nullable=True)
    dream_outcome = mapped_column(JSON, nullable=True)
    objections = mapped_column(JSON, nullable=True)        # [{objection, rebuttal}]
    buying_triggers = mapped_column(JSON, nullable=True)
    identity = mapped_column(JSON, nullable=True)          # {self_image, aspiration, tribe}
    lifestyle = mapped_column(JSON, nullable=True)
    language = mapped_column(JSON, nullable=True)          # verbatim phrases they use
    behavior = mapped_column(JSON, nullable=True)          # {channels, content, buying_habits}
    jobs_to_be_done = mapped_column(JSON, nullable=True)   # [{job, context, outcome}]
    emotional_triggers = mapped_column(JSON, nullable=True)
    targeting = mapped_column(JSON, nullable=True)         # Meta targeting suggestion

    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# Module 10 — Research Engine  +  RAG knowledge store
# ─────────────────────────────────────────────────────────────────────────────
class ResearchJob(Base):
    __tablename__ = "research_jobs"
    __table_args__ = (Index("idx_research_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    query = mapped_column(String(500), nullable=False)
    sources = mapped_column(JSON, nullable=False)          # ["reddit","youtube","reviews","amazon",...]
    status = mapped_column(String(16), default="PENDING", nullable=False)
    results = mapped_column(JSON, nullable=True)           # per-source findings
    summary = mapped_column(Text, nullable=True)
    insights = mapped_column(JSON, nullable=True)          # [{insight, evidence, marketing_use}]
    voice_of_customer = mapped_column(JSON, nullable=True) # verbatim phrases mined for copy
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    finished_at = mapped_column(DateTime(timezone=True), nullable=True)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (Index("idx_knowdoc_client_ns", "client_id", "namespace"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    namespace = mapped_column(String(40), default="general", nullable=False)
    # general|business|research|campaigns|creatives|performance|brand
    title = mapped_column(String(300), nullable=False)
    source_type = mapped_column(String(20), default="text", nullable=False)  # url|pdf|csv|text|shopify|manual
    source_url = mapped_column(String(600), nullable=True)
    content = mapped_column(Text, nullable=False)
    meta = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    chunks = relationship("EmbeddingChunk", back_populates="document", cascade="all, delete-orphan")


class EmbeddingChunk(Base):
    __tablename__ = "embedding_chunks"
    __table_args__ = (Index("idx_chunk_client_ns", "client_id", "namespace"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id = mapped_column(String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    client_id = mapped_column(String(36), nullable=False)
    namespace = mapped_column(String(40), default="general", nullable=False)
    chunk_index = mapped_column(Integer, default=0, nullable=False)
    content = mapped_column(Text, nullable=False)
    token_count = mapped_column(Integer, default=0, nullable=False)
    # Portable storage; on Postgres a parallel `embedding_vec vector(N)` column
    # is added by the migration and kept in sync by the vector store.
    embedding = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")


# ─────────────────────────────────────────────────────────────────────────────
# Modules 4 & 5 — Creative Intelligence + Visual AI
# ─────────────────────────────────────────────────────────────────────────────
class CreativeAsset(Base):
    __tablename__ = "creative_assets"
    __table_args__ = (Index("idx_creative_client_kind", "client_id", "kind"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    persona_id = mapped_column(String(36), ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)
    batch_id = mapped_column(String(36), nullable=True)    # groups one generation run
    kind = mapped_column(String(24), nullable=False)
    # hook|headline|angle|primary_text|ugc_concept|reel_concept|image_concept|carousel|script|cta
    framework = mapped_column(String(24), default="AIDA", nullable=False)
    # AIDA|PAS|BAB|STORY|UGC|FOUNDER|AUTHORITY|PROBLEM|CURIOSITY|SHOCK|COMPARISON|TESTIMONIAL|CASE_STUDY
    content = mapped_column(Text, nullable=False)
    meta = mapped_column(JSON, nullable=True)              # {angle, awareness_level, cta, visual_direction}
    predicted_score = mapped_column(Float, default=0, nullable=False)
    status = mapped_column(String(16), default="DRAFT", nullable=False)  # DRAFT|APPROVED|IN_USE|RETIRED|WINNER
    performance = mapped_column(JSON, nullable=True)       # backfilled from ads
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class VisualAnalysis(Base):
    __tablename__ = "visual_analyses"
    __table_args__ = (Index("idx_visual_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    asset_url = mapped_column(String(600), nullable=False)
    kind = mapped_column(String(16), default="image", nullable=False)   # image|video|product|packaging
    creative_score = mapped_column(Integer, default=0, nullable=False)
    attention_score = mapped_column(Integer, default=0, nullable=False)
    scroll_stop_score = mapped_column(Integer, default=0, nullable=False)
    brand_score = mapped_column(Integer, default=0, nullable=False)
    emotion_score = mapped_column(Integer, default=0, nullable=False)
    ctr_prediction = mapped_column(Float, default=0, nullable=False)
    recommendations = mapped_column(JSON, nullable=True)
    raw = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# Module 6 — Campaign Builder
# ─────────────────────────────────────────────────────────────────────────────
class CampaignBlueprint(Base):
    __tablename__ = "campaign_blueprints"
    __table_args__ = (Index("idx_blueprint_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = mapped_column(String(240), nullable=False)
    objective = mapped_column(String(40), default="OUTCOME_SALES", nullable=False)
    status = mapped_column(String(16), default="DRAFT", nullable=False)  # DRAFT|READY|PUBLISHING|PUBLISHED|FAILED
    daily_budget = mapped_column(Float, default=0, nullable=False)
    structure = mapped_column(JSON, nullable=True)         # {campaign, ad_sets:[{ads:[...]}]}
    naming = mapped_column(JSON, nullable=True)            # naming convention used
    budget_plan = mapped_column(JSON, nullable=True)       # {split, rationale, guardrails}
    audience_strategy = mapped_column(JSON, nullable=True)
    placements = mapped_column(JSON, nullable=True)
    pixel_mapping = mapped_column(JSON, nullable=True)     # {pixel_id, events:{...}}
    creative_rotation = mapped_column(JSON, nullable=True)
    scaling_plan = mapped_column(JSON, nullable=True)      # {horizontal, vertical, triggers}
    published_ids = mapped_column(JSON, nullable=True)     # Meta ids after launch
    rationale = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# Multi-agent orchestration
# ─────────────────────────────────────────────────────────────────────────────
class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (Index("idx_agentrun_client_kind", "client_id", "kind"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    kind = mapped_column(String(40), nullable=False)
    # business_analysis|competitor_analysis|audience|creative_batch|campaign_plan|
    # performance_review|optimization|research|morning_report|strategy_council
    status = mapped_column(String(16), default="PENDING", nullable=False)  # PENDING|RUNNING|DONE|FAILED
    input = mapped_column(JSON, nullable=True)
    steps = mapped_column(JSON, nullable=True)             # [{agent, action, at, summary}]
    messages = mapped_column(JSON, nullable=True)          # full debate transcript
    votes = mapped_column(JSON, nullable=True)             # [{agent, option, confidence, reason}]
    decision = mapped_column(JSON, nullable=True)          # final synthesized output
    error = mapped_column(Text, nullable=True)
    tokens_in = mapped_column(Integer, default=0, nullable=False)
    tokens_out = mapped_column(Integer, default=0, nullable=False)
    cost_usd = mapped_column(Float, default=0, nullable=False)
    started_at = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class UsageLedger(Base):
    __tablename__ = "usage_ledger"
    __table_args__ = (Index("idx_usage_client_date", "client_id", "date"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), nullable=True)
    date = mapped_column(Date, nullable=False)
    provider = mapped_column(String(20), nullable=False)   # openai|anthropic|gemini|mock
    model = mapped_column(String(60), nullable=False)
    tokens_in = mapped_column(Integer, default=0, nullable=False)
    tokens_out = mapped_column(Integer, default=0, nullable=False)
    cost_usd = mapped_column(Float, default=0, nullable=False)
    kind = mapped_column(String(40), default="llm", nullable=False)  # llm|embedding|vision


# ─────────────────────────────────────────────────────────────────────────────
# Predictive AI + Scoring
# ─────────────────────────────────────────────────────────────────────────────
class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (Index("idx_prediction_entity", "entity_type", "entity_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    entity_type = mapped_column(String(24), nullable=False)  # creative|blueprint|campaign|audience
    entity_id = mapped_column(String(36), nullable=False)
    ctr = mapped_column(Float, default=0, nullable=False)
    cvr = mapped_column(Float, default=0, nullable=False)
    cpa = mapped_column(Float, default=0, nullable=False)
    roas = mapped_column(Float, default=0, nullable=False)
    creative_quality = mapped_column(Float, default=0, nullable=False)
    win_probability = mapped_column(Float, default=0, nullable=False)
    audience_match = mapped_column(Float, default=0, nullable=False)
    features = mapped_column(JSON, nullable=True)
    model_version = mapped_column(String(40), default="heuristic-v1", nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class CampaignScore(Base):
    __tablename__ = "campaign_scores"
    __table_args__ = (Index("idx_campscore_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    campaign_id = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=True)
    blueprint_id = mapped_column(String(36), ForeignKey("campaign_blueprints.id", ondelete="CASCADE"), nullable=True)
    date = mapped_column(Date, nullable=False)
    overall = mapped_column(Integer, default=0, nullable=False)
    creative = mapped_column(Integer, default=0, nullable=False)
    audience = mapped_column(Integer, default=0, nullable=False)
    offer = mapped_column(Integer, default=0, nullable=False)
    landing_page = mapped_column(Integer, default=0, nullable=False)
    tracking = mapped_column(Integer, default=0, nullable=False)
    brand = mapped_column(Integer, default=0, nullable=False)
    scaling = mapped_column(Integer, default=0, nullable=False)
    details = mapped_column(JSON, nullable=True)           # per-dimension reasons + fixes


# ─────────────────────────────────────────────────────────────────────────────
# Modules 8 & 9 — Optimization
# ─────────────────────────────────────────────────────────────────────────────
class FatigueSignal(Base):
    __tablename__ = "fatigue_signals"
    __table_args__ = (Index("idx_fatigue_client_resolved", "client_id", "resolved"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    entity_type = mapped_column(String(20), nullable=False)   # creative|audience|offer|ad|campaign
    entity_ref = mapped_column(String(240), nullable=False)   # name or id
    fatigue_type = mapped_column(String(20), nullable=False)  # creative|audience|offer|ad
    severity = mapped_column(String(10), default="WARNING", nullable=False)  # INFO|WARNING|CRITICAL
    evidence = mapped_column(JSON, nullable=True)             # {frequency, ctr_trend, cpa_trend, days_running}
    recommendation = mapped_column(Text, nullable=True)
    resolved = mapped_column(Boolean, default=False, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class OptimizationAction(Base):
    __tablename__ = "optimization_actions"
    __table_args__ = (Index("idx_optaction_client_status", "client_id", "status"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    campaign_id = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    campaign_ref = mapped_column(String(240), nullable=False)
    action = mapped_column(String(24), nullable=False)
    # increase_budget|decrease_budget|duplicate|kill|scale_vertical|scale_horizontal|budget_split|refresh_creative
    amount = mapped_column(JSON, nullable=True)            # {from, to, pct}
    reason = mapped_column(Text, nullable=False)
    confidence = mapped_column(Float, default=0.5, nullable=False)
    expected_impact = mapped_column(String(300), nullable=True)
    status = mapped_column(String(16), default="PROPOSED", nullable=False)  # PROPOSED|APPROVED|APPLIED|DISMISSED
    applied_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# Automations + Billing
# ─────────────────────────────────────────────────────────────────────────────
class AutomationRun(Base):
    __tablename__ = "automation_runs"
    __table_args__ = (Index("idx_automation_kind", "kind", "created_at"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=True)
    kind = mapped_column(String(40), nullable=False)  # morning_report|fatigue_scan|budget_review|creative_refresh
    status = mapped_column(String(16), default="DONE", nullable=False)
    output = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("client_id", name="uq_subscription_client"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    stripe_customer_id = mapped_column(String(120), nullable=True)
    stripe_subscription_id = mapped_column(String(120), nullable=True)
    plan = mapped_column(String(20), default="STARTER", nullable=False)  # STARTER|GROWTH|SCALE
    status = mapped_column(String(20), default="TRIALING", nullable=False)
    # TRIALING|ACTIVE|PAST_DUE|CANCELED
    current_period_end = mapped_column(DateTime(timezone=True), nullable=True)
    meta = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)
