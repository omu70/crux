"""Client dashboard: profile summary, KPI cards, chart timeseries, scores."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_client
from app.models import (
    Alert, Client, MetricSnapshot, PerformanceScore, WebsiteHealth,
)
from app.services.kpi import aggregate, build_kpi_cards, resolve_range

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _metrics_between(db: Session, client_id: str, start: dt.date, end: dt.date):
    return (
        db.query(MetricSnapshot)
        .filter(MetricSnapshot.client_id == client_id,
                MetricSnapshot.date >= start, MetricSnapshot.date <= end)
        .order_by(MetricSnapshot.date.asc())
        .all()
    )


def _greeting(now: dt.datetime) -> str:
    h = now.hour
    if h < 12:
        return "Good Morning"
    if h < 17:
        return "Good Afternoon"
    return "Good Evening"


@router.get("/summary")
def summary(range: str = "30d", db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    start, end, pstart, pend = resolve_range(range)
    cur = aggregate(_metrics_between(db, client.id, start, end))
    prev = aggregate(_metrics_between(db, client.id, pstart, pend))
    now = dt.datetime.now(dt.timezone.utc)
    return {
        "greeting": _greeting(now),
        "client": {
            "company_name": client.company_name,
            "contact_name": client.contact_name,
            "plan": client.plan,
            "monthly_budget": client.monthly_budget,
            "currency": client.currency,
            "current_month": now.strftime("%B %Y"),
            "account_manager": {
                "name": client.account_manager.name,
                "title": client.account_manager.title,
                "email": client.account_manager.email,
                "avatar_url": client.account_manager.avatar_url,
            } if client.account_manager else None,
            "targets": {
                "revenue": client.monthly_target_revenue,
                "roas": client.monthly_target_roas,
                "leads": client.monthly_target_leads,
            },
        },
        "range": {"start": start.isoformat(), "end": end.isoformat(), "key": range},
        "kpis": build_kpi_cards(cur, prev),
    }


@router.get("/kpis")
def kpis(
    range: str = "30d",
    date_from: Optional[dt.date] = Query(None),
    date_to: Optional[dt.date] = Query(None),
    db: Session = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    start, end, pstart, pend = resolve_range(range, date_from, date_to)
    cur = aggregate(_metrics_between(db, client.id, start, end))
    prev = aggregate(_metrics_between(db, client.id, pstart, pend))
    return {"range": {"start": start.isoformat(), "end": end.isoformat()},
            "kpis": build_kpi_cards(cur, prev)}


@router.get("/timeseries")
def timeseries(
    metrics: str = Query("revenue", description="Comma-separated metric keys"),
    range: str = "30d",
    date_from: Optional[dt.date] = Query(None),
    date_to: Optional[dt.date] = Query(None),
    db: Session = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    start, end, _ps, _pe = resolve_range(range, date_from, date_to)
    rows = _metrics_between(db, client.id, start, end)
    keys = [k.strip() for k in metrics.split(",") if k.strip()]
    series = [
        {"date": r.date.isoformat(), **{k: getattr(r, k, 0) for k in keys}}
        for r in rows
    ]
    return {"metrics": keys, "series": series}


@router.get("/performance-score")
def performance_score(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    row = (db.query(PerformanceScore)
           .filter(PerformanceScore.client_id == client.id)
           .order_by(PerformanceScore.date.desc()).first())
    if row is None:
        return {"overall": 0, "breakdown": {}}
    return {
        "overall": row.overall,
        "date": row.date.isoformat(),
        "breakdown": {
            "Ads": row.ads_score, "SEO": row.seo_score, "Website": row.website_score,
            "Revenue": row.revenue_score, "Speed": row.speed_score, "Conversion": row.conversion_score,
        },
    }


@router.get("/website-health")
def website_health(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    row = (db.query(WebsiteHealth)
           .filter(WebsiteHealth.client_id == client.id)
           .order_by(WebsiteHealth.date.desc()).first())
    if row is None:
        return {}
    return {
        "date": row.date.isoformat(),
        "performance": row.performance, "accessibility": row.accessibility,
        "seo": row.seo, "best_practices": row.best_practices,
        "core_web_vitals": {"lcp": row.lcp, "fid": row.fid, "cls": row.cls},
    }


@router.get("/alerts")
def alerts(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(Alert)
            .filter(Alert.client_id == client.id, Alert.resolved == False)  # noqa: E712
            .order_by(Alert.created_at.desc()).all())
    return [{"id": a.id, "type": a.type, "severity": a.severity, "title": a.title,
             "message": a.message, "created_at": a.created_at.isoformat()} for a in rows]
