"""SQLAlchemy models — a 1:1 mirror of prisma/schema.prisma.

Portable column types (String ids, String enums, JSON) so the same models run
on PostgreSQL (Supabase / Docker) and SQLite (dev / tests).
"""
from __future__ import annotations

import datetime as dt
from uuid import uuid4

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, JSON,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid4())


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    email = mapped_column(String(255), unique=True, nullable=False)
    username = mapped_column(String(120), unique=True, nullable=False)
    password_hash = mapped_column(String(255), nullable=False)
    role = mapped_column(String(16), default="CLIENT", nullable=False)
    is_active = mapped_column(Boolean, default=True, nullable=False)
    last_login_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    client = relationship("Client", back_populates="user", uselist=False, cascade="all, delete-orphan")


class AccountManager(Base):
    __tablename__ = "account_managers"

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    name = mapped_column(String(180), nullable=False)
    email = mapped_column(String(255), unique=True, nullable=False)
    title = mapped_column(String(120), default="Account Manager", nullable=False)
    avatar_url = mapped_column(String(500), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    clients = relationship("Client", back_populates="account_manager")


class Client(Base):
    __tablename__ = "clients"

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name = mapped_column(String(200), nullable=False)
    contact_name = mapped_column(String(200), nullable=False)
    plan = mapped_column(String(60), default="Growth", nullable=False)
    status = mapped_column(String(16), default="ACTIVE", nullable=False)
    currency = mapped_column(String(8), default="USD", nullable=False)
    timezone = mapped_column(String(60), default="UTC", nullable=False)
    logo_url = mapped_column(String(500), nullable=True)
    monthly_budget = mapped_column(Float, default=0, nullable=False)
    monthly_target_revenue = mapped_column(Float, default=0, nullable=False)
    monthly_target_roas = mapped_column(Float, default=0, nullable=False)
    monthly_target_leads = mapped_column(Integer, default=0, nullable=False)
    account_manager_id = mapped_column(String(36), ForeignKey("account_managers.id"), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    user = relationship("User", back_populates="client")
    account_manager = relationship("AccountManager", back_populates="clients")
    integrations = relationship("Integration", back_populates="client", cascade="all, delete-orphan")
    metrics = relationship("MetricSnapshot", back_populates="client", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="client", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="client", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="client", cascade="all, delete-orphan")
    analytics = relationship("AnalyticsSnapshot", back_populates="client", cascade="all, delete-orphan")
    search_console = relationship("SearchConsoleSnapshot", back_populates="client", cascade="all, delete-orphan")
    seo = relationship("SeoSnapshot", back_populates="client", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="client", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="client", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="client", cascade="all, delete-orphan")
    meeting_notes = relationship("MeetingNote", back_populates="client", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="client", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="client", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="client", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="client", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="client", cascade="all, delete-orphan")
    insights = relationship("AiInsight", back_populates="client", cascade="all, delete-orphan")
    scores = relationship("PerformanceScore", back_populates="client", cascade="all, delete-orphan")
    website_health = relationship("WebsiteHealth", back_populates="client", cascade="all, delete-orphan")


class Integration(Base):
    __tablename__ = "integrations"
    __table_args__ = (UniqueConstraint("client_id", "type", name="uq_integration_client_type"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    type = mapped_column(String(24), nullable=False)
    status = mapped_column(String(16), default="PENDING", nullable=False)
    external_id = mapped_column(String(200), nullable=True)
    account_name = mapped_column(String(200), nullable=True)
    config = mapped_column(JSON, nullable=True)
    last_synced_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="integrations")


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        UniqueConstraint("client_id", "date", name="uq_metric_client_date"),
        Index("idx_metric_client_date", "client_id", "date"),
    )

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(Date, nullable=False)
    revenue = mapped_column(Float, default=0, nullable=False)
    orders = mapped_column(Integer, default=0, nullable=False)
    ad_spend = mapped_column(Float, default=0, nullable=False)
    roas = mapped_column(Float, default=0, nullable=False)
    ctr = mapped_column(Float, default=0, nullable=False)
    cpa = mapped_column(Float, default=0, nullable=False)
    cpm = mapped_column(Float, default=0, nullable=False)
    conversion_rate = mapped_column(Float, default=0, nullable=False)
    aov = mapped_column(Float, default=0, nullable=False)
    revenue_growth = mapped_column(Float, default=0, nullable=False)
    sessions = mapped_column(Integer, default=0, nullable=False)
    returning_customers = mapped_column(Integer, default=0, nullable=False)
    new_customers = mapped_column(Integer, default=0, nullable=False)
    profit_estimate = mapped_column(Float, default=0, nullable=False)
    lead_count = mapped_column(Integer, default=0, nullable=False)
    whatsapp_leads = mapped_column(Integer, default=0, nullable=False)
    phone_calls = mapped_column(Integer, default=0, nullable=False)
    impressions = mapped_column(Integer, default=0, nullable=False)
    clicks = mapped_column(Integer, default=0, nullable=False)
    reach = mapped_column(Integer, default=0, nullable=False)

    client = relationship("Client", back_populates="metrics")


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (Index("idx_campaign_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    external_id = mapped_column(String(120), nullable=True)
    name = mapped_column(String(200), nullable=False)
    status = mapped_column(String(16), default="ACTIVE", nullable=False)
    objective = mapped_column(String(60), default="CONVERSIONS", nullable=False)
    spend = mapped_column(Float, default=0, nullable=False)
    reach = mapped_column(Integer, default=0, nullable=False)
    frequency = mapped_column(Float, default=0, nullable=False)
    ctr = mapped_column(Float, default=0, nullable=False)
    clicks = mapped_column(Integer, default=0, nullable=False)
    impressions = mapped_column(Integer, default=0, nullable=False)
    cpm = mapped_column(Float, default=0, nullable=False)
    cpa = mapped_column(Float, default=0, nullable=False)
    conversions = mapped_column(Integer, default=0, nullable=False)
    purchase_roas = mapped_column(Float, default=0, nullable=False)
    revenue = mapped_column(Float, default=0, nullable=False)
    is_winning = mapped_column(Boolean, default=False, nullable=False)
    is_losing = mapped_column(Boolean, default=False, nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    client = relationship("Client", back_populates="campaigns")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (Index("idx_order_client_created", "client_id", "created_at"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    external_id = mapped_column(String(120), nullable=True)
    order_number = mapped_column(String(60), nullable=False)
    customer_name = mapped_column(String(200), nullable=False)
    total = mapped_column(Float, default=0, nullable=False)
    status = mapped_column(String(16), default="PAID", nullable=False)
    items_count = mapped_column(Integer, default=1, nullable=False)
    source = mapped_column(String(30), default="shopify", nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="orders")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (Index("idx_product_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    external_id = mapped_column(String(120), nullable=True)
    title = mapped_column(String(240), nullable=False)
    category = mapped_column(String(120), default="General", nullable=False)
    price = mapped_column(Float, default=0, nullable=False)
    units_sold = mapped_column(Integer, default=0, nullable=False)
    revenue = mapped_column(Float, default=0, nullable=False)
    inventory = mapped_column(Integer, default=0, nullable=False)
    low_stock = mapped_column(Boolean, default=False, nullable=False)

    client = relationship("Client", back_populates="products")


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (UniqueConstraint("client_id", "date", name="uq_analytics_client_date"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(Date, nullable=False)
    visitors = mapped_column(Integer, default=0, nullable=False)
    sessions = mapped_column(Integer, default=0, nullable=False)
    bounce_rate = mapped_column(Float, default=0, nullable=False)
    engagement_time = mapped_column(Float, default=0, nullable=False)
    organic = mapped_column(Integer, default=0, nullable=False)
    paid = mapped_column(Integer, default=0, nullable=False)
    direct = mapped_column(Integer, default=0, nullable=False)
    referral = mapped_column(Integer, default=0, nullable=False)
    top_countries = mapped_column(JSON, nullable=True)
    top_cities = mapped_column(JSON, nullable=True)
    devices = mapped_column(JSON, nullable=True)
    browsers = mapped_column(JSON, nullable=True)

    client = relationship("Client", back_populates="analytics")


class SearchConsoleSnapshot(Base):
    __tablename__ = "search_console_snapshots"
    __table_args__ = (UniqueConstraint("client_id", "date", name="uq_gsc_client_date"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(Date, nullable=False)
    clicks = mapped_column(Integer, default=0, nullable=False)
    impressions = mapped_column(Integer, default=0, nullable=False)
    avg_position = mapped_column(Float, default=0, nullable=False)
    ctr = mapped_column(Float, default=0, nullable=False)
    top_keywords = mapped_column(JSON, nullable=True)
    top_pages = mapped_column(JSON, nullable=True)

    client = relationship("Client", back_populates="search_console")


class SeoSnapshot(Base):
    __tablename__ = "seo_snapshots"
    __table_args__ = (UniqueConstraint("client_id", "date", name="uq_seo_client_date"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(Date, nullable=False)
    keyword_growth = mapped_column(Float, default=0, nullable=False)
    backlinks = mapped_column(Integer, default=0, nullable=False)
    indexed_pages = mapped_column(Integer, default=0, nullable=False)
    technical_issues = mapped_column(Integer, default=0, nullable=False)
    suggestions = mapped_column(JSON, nullable=True)

    client = relationship("Client", back_populates="seo")


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (Index("idx_report_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    title = mapped_column(String(240), nullable=False)
    month = mapped_column(String(20), nullable=False)
    summary = mapped_column(Text, nullable=False)
    wins = mapped_column(JSON, nullable=True)
    losses = mapped_column(JSON, nullable=True)
    kpis = mapped_column(JSON, nullable=True)
    suggestions = mapped_column(JSON, nullable=True)
    strategy = mapped_column(Text, nullable=True)
    file_url = mapped_column(String(500), nullable=True)
    created_by = mapped_column(String(120), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="reports")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (Index("idx_task_client_status", "client_id", "status"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    title = mapped_column(String(240), nullable=False)
    description = mapped_column(Text, nullable=True)
    status = mapped_column(String(16), default="PENDING", nullable=False)
    priority = mapped_column(String(10), default="MEDIUM", nullable=False)
    due_date = mapped_column(DateTime(timezone=True), nullable=True)
    responsible = mapped_column(String(120), nullable=True)
    expected_result = mapped_column(String(400), nullable=True)
    timeframe = mapped_column(String(12), default="week", nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="tasks")


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (Index("idx_goal_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    type = mapped_column(String(12), nullable=False)
    label = mapped_column(String(160), nullable=False)
    target = mapped_column(Float, nullable=False)
    current = mapped_column(Float, default=0, nullable=False)
    unit = mapped_column(String(16), default="", nullable=False)
    period = mapped_column(String(16), default="month", nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="goals")


class MeetingNote(Base):
    __tablename__ = "meeting_notes"
    __table_args__ = (Index("idx_meeting_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    title = mapped_column(String(240), nullable=False)
    notes = mapped_column(Text, nullable=False)
    action_items = mapped_column(JSON, nullable=True)
    recording_url = mapped_column(String(500), nullable=True)
    meeting_date = mapped_column(DateTime(timezone=True), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="meeting_notes")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("idx_notification_client_read", "client_id", "read"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    type = mapped_column(String(30), default="GENERAL", nullable=False)
    title = mapped_column(String(240), nullable=False)
    message = mapped_column(Text, nullable=False)
    read = mapped_column(Boolean, default=False, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="notifications")


class Announcement(Base):
    __tablename__ = "announcements"

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    title = mapped_column(String(240), nullable=False)
    message = mapped_column(Text, nullable=False)
    created_by = mapped_column(String(120), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index("idx_document_client_category", "client_id", "category"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = mapped_column(String(240), nullable=False)
    category = mapped_column(String(16), default="OTHER", nullable=False)
    file_type = mapped_column(String(30), nullable=False)
    file_url = mapped_column(String(500), nullable=False)
    size_bytes = mapped_column(Integer, default=0, nullable=False)
    uploaded_by = mapped_column(String(120), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="documents")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (Index("idx_ticket_client_status", "client_id", "status"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    subject = mapped_column(String(240), nullable=False)
    description = mapped_column(Text, nullable=False)
    priority = mapped_column(String(10), default="MEDIUM", nullable=False)
    status = mapped_column(String(16), default="OPEN", nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    client = relationship("Client", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    __table_args__ = (Index("idx_ticketmsg_ticket", "ticket_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    ticket_id = mapped_column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    sender_id = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    body = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    ticket = relationship("Ticket", back_populates="messages")
    sender = relationship("User")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("idx_chat_client_created", "client_id", "created_at"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    sender_id = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    sender_role = mapped_column(String(16), nullable=False)
    body = mapped_column(Text, nullable=False)
    read_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="chat_messages")
    sender = relationship("User")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("idx_alert_client_resolved", "client_id", "resolved"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    type = mapped_column(String(30), nullable=False)
    severity = mapped_column(String(10), default="WARNING", nullable=False)
    title = mapped_column(String(240), nullable=False)
    message = mapped_column(Text, nullable=False)
    resolved = mapped_column(Boolean, default=False, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="alerts")


class AiInsight(Base):
    __tablename__ = "ai_insights"
    __table_args__ = (Index("idx_insight_client", "client_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    title = mapped_column(String(240), nullable=False)
    body = mapped_column(Text, nullable=False)
    category = mapped_column(String(20), default="performance", nullable=False)
    impact = mapped_column(String(10), default="MEDIUM", nullable=False)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)

    client = relationship("Client", back_populates="insights")


class PerformanceScore(Base):
    __tablename__ = "performance_scores"
    __table_args__ = (UniqueConstraint("client_id", "date", name="uq_score_client_date"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(Date, nullable=False)
    overall = mapped_column(Integer, default=0, nullable=False)
    ads_score = mapped_column(Integer, default=0, nullable=False)
    seo_score = mapped_column(Integer, default=0, nullable=False)
    website_score = mapped_column(Integer, default=0, nullable=False)
    revenue_score = mapped_column(Integer, default=0, nullable=False)
    speed_score = mapped_column(Integer, default=0, nullable=False)
    conversion_score = mapped_column(Integer, default=0, nullable=False)

    client = relationship("Client", back_populates="scores")


class WebsiteHealth(Base):
    __tablename__ = "website_health"
    __table_args__ = (UniqueConstraint("client_id", "date", name="uq_health_client_date"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id = mapped_column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(Date, nullable=False)
    performance = mapped_column(Integer, default=0, nullable=False)
    accessibility = mapped_column(Integer, default=0, nullable=False)
    seo = mapped_column(Integer, default=0, nullable=False)
    best_practices = mapped_column(Integer, default=0, nullable=False)
    lcp = mapped_column(Float, default=0, nullable=False)
    fid = mapped_column(Float, default=0, nullable=False)
    cls = mapped_column(Float, default=0, nullable=False)

    client = relationship("Client", back_populates="website_health")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("idx_audit_user", "user_id"),)

    id = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action = mapped_column(String(120), nullable=False)
    entity = mapped_column(String(60), nullable=True)
    entity_id = mapped_column(String(60), nullable=True)
    ip = mapped_column(String(60), nullable=True)
    meta = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
