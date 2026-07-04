"""AI insights, next-plan-of-action, and monthly reports."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_client
from app.models import AiInsight, Client, MetricSnapshot, Report, Task
from app.services.ai import generate_insights, generate_plan_of_action

router = APIRouter(prefix="/api", tags=["insights"])


def _recent_metric_dicts(db: Session, client_id: str, days: int = 30):
    since = dt.date.today() - dt.timedelta(days=days)
    rows = (db.query(MetricSnapshot)
            .filter(MetricSnapshot.client_id == client_id, MetricSnapshot.date >= since)
            .order_by(MetricSnapshot.date.asc()).all())
    keys = ("revenue", "orders", "ad_spend", "roas", "ctr", "cpa", "conversion_rate", "aov")
    return [{"date": r.date.isoformat(), **{k: getattr(r, k) for k in keys}} for r in rows]


@router.get("/insights")
def list_insights(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(AiInsight).filter(AiInsight.client_id == client.id)
            .order_by(AiInsight.created_at.desc()).limit(12).all())
    if rows:
        return [{"id": r.id, "title": r.title, "body": r.body, "category": r.category,
                 "impact": r.impact, "created_at": r.created_at.isoformat()} for r in rows]
    # None stored yet — generate on the fly (without persisting).
    metrics = _recent_metric_dicts(db, client.id)
    return generate_insights(client.company_name, metrics)


@router.post("/insights/generate")
def generate(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    metrics = _recent_metric_dicts(db, client.id)
    fresh = generate_insights(client.company_name, metrics)
    # Replace today's set.
    for ins in fresh:
        db.add(AiInsight(client_id=client.id, title=ins["title"], body=ins["body"],
                         category=ins.get("category", "performance"), impact=ins.get("impact", "MEDIUM")))
    db.commit()
    return {"generated": len(fresh), "insights": fresh}


@router.get("/insights/plan")
def plan_of_action(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    """Return the agency-authored plan (Tasks grouped by timeframe). Falls back
    to an auto-generated plan only when no tasks have been created yet."""
    tasks = (db.query(Task).filter(Task.client_id == client.id)
             .order_by(Task.created_at.desc()).all())
    buckets: dict[str, list] = {"today": [], "week": [], "month": []}
    for t in tasks:
        tf = t.timeframe if t.timeframe in buckets else "week"
        buckets[tf].append({
            "title": t.title,
            "priority": t.priority,
            "expected_result": t.expected_result or t.description or "",
            "status": t.status,
        })
    if any(buckets.values()):
        return buckets
    return generate_plan_of_action(_recent_metric_dicts(db, client.id))


@router.get("/reports")
def list_reports(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(Report).filter(Report.client_id == client.id)
            .order_by(Report.created_at.desc()).all())
    return [{"id": r.id, "title": r.title, "month": r.month, "summary": r.summary,
             "file_url": r.file_url, "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/reports/{report_id}")
def report_detail(report_id: str, db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    r = db.get(Report, report_id)
    if r is None or r.client_id != client.id:
        return {}
    return {
        "id": r.id, "title": r.title, "month": r.month, "summary": r.summary,
        "wins": r.wins or [], "losses": r.losses or [], "kpis": r.kpis or {},
        "suggestions": r.suggestions or [], "strategy": r.strategy,
        "file_url": r.file_url, "created_at": r.created_at.isoformat(),
    }
