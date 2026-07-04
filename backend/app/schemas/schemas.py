"""Pydantic request/response schemas."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Auth ─────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str
    remember: bool = False


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(ORMModel):
    id: str
    email: EmailStr
    username: str
    role: str
    is_active: bool
    last_login_at: Optional[dt.datetime] = None


# ── Account manager ──────────────────────────────────────────────────────────
class AccountManagerOut(ORMModel):
    id: str
    name: str
    email: EmailStr
    title: str
    avatar_url: Optional[str] = None


# ── Clients ──────────────────────────────────────────────────────────────────
class ClientCreate(BaseModel):
    company_name: str
    contact_name: str
    username: str
    password: str = Field(min_length=8)
    email: EmailStr
    plan: str = "Growth"
    monthly_budget: float = 0
    monthly_target_revenue: float = 0
    monthly_target_roas: float = 0
    monthly_target_leads: int = 0
    account_manager_id: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"


class ClientUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    plan: Optional[str] = None
    status: Optional[str] = None
    monthly_budget: Optional[float] = None
    monthly_target_revenue: Optional[float] = None
    monthly_target_roas: Optional[float] = None
    monthly_target_leads: Optional[int] = None
    account_manager_id: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None


class ClientCredentials(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)


class ClientOut(ORMModel):
    id: str
    company_name: str
    contact_name: str
    plan: str
    status: str
    currency: str
    timezone: str
    logo_url: Optional[str] = None
    monthly_budget: float
    monthly_target_revenue: float
    monthly_target_roas: float
    monthly_target_leads: int
    account_manager: Optional[AccountManagerOut] = None
    user: Optional[UserOut] = None
    created_at: dt.datetime


# ── Integrations ─────────────────────────────────────────────────────────────
class IntegrationConnect(BaseModel):
    type: str
    external_id: Optional[str] = None
    account_name: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    status: str = "CONNECTED"


class IntegrationOut(ORMModel):
    id: str
    type: str
    status: str
    external_id: Optional[str] = None
    account_name: Optional[str] = None
    last_synced_at: Optional[dt.datetime] = None


# ── Metrics ──────────────────────────────────────────────────────────────────
class MetricOut(ORMModel):
    date: dt.date
    revenue: float
    orders: int
    ad_spend: float
    roas: float
    ctr: float
    cpa: float
    cpm: float
    conversion_rate: float
    aov: float
    revenue_growth: float
    sessions: int
    returning_customers: int
    new_customers: int
    profit_estimate: float
    lead_count: int
    whatsapp_leads: int
    phone_calls: int
    impressions: int
    clicks: int
    reach: int


class KpiCard(BaseModel):
    key: str
    label: str
    value: float
    unit: str = ""
    delta: float = 0.0          # percent change vs comparison period
    format: str = "number"      # number | currency | percent | ratio


# ── Tasks / goals / etc. (generic create bodies) ─────────────────────────────
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "PENDING"
    priority: str = "MEDIUM"
    due_date: Optional[dt.datetime] = None
    responsible: Optional[str] = None
    expected_result: Optional[str] = None
    timeframe: str = "week"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[dt.datetime] = None
    responsible: Optional[str] = None
    expected_result: Optional[str] = None
    timeframe: Optional[str] = None


class GoalCreate(BaseModel):
    type: str
    label: str
    target: float
    current: float = 0
    unit: str = ""
    period: str = "month"


class NotificationCreate(BaseModel):
    client_id: Optional[str] = None      # None ⇒ broadcast to all clients
    type: str = "GENERAL"
    title: str
    message: str


class AnnouncementCreate(BaseModel):
    title: str
    message: str


class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: str = "MEDIUM"


class TicketReply(BaseModel):
    body: str


class TicketStatusUpdate(BaseModel):
    status: str


class ChatSend(BaseModel):
    body: str


class MeetingNoteCreate(BaseModel):
    title: str
    notes: str
    action_items: Optional[list[str]] = None
    recording_url: Optional[str] = None
    meeting_date: dt.datetime


class GenericOK(BaseModel):
    ok: bool = True
    id: Optional[str] = None
