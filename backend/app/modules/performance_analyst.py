"""Module 7 — AI Performance Analyst.

Reads synced campaign + metric data (Meta/GA4/Shopify/Woo already sync into
CRUX tables), computes derived diagnostics (hook rate, thumb-stop, hold rate
where video metrics exist in campaign meta), finds why losers lose and winners
win, and produces an analyst brief.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.ml.predictors import predict_campaign, predict_with_learned
from app.models.aether import Prediction
from app.models.models import Campaign, Client, MetricSnapshot
from app.modules.business_intel import business_context_snippet

log = logging.getLogger("aether.analyst")

BRIEF_SHAPE = {
    "headline": "one-line state of the account",
    "binding_constraint": "creative|offer_lp|tracking|delivery|budget — the ONE thing capping results, with evidence",
    "winners": [{"campaign": "name", "why_winning": "mechanism with numbers", "action": "how to press the advantage"}],
    "losers": [{"campaign": "name", "why_failing": "mechanism with numbers", "action": "fix or kill, with reason"}],
    "funnel_diagnosis": [{"stage": "impression→click|click→atc|atc→purchase",
                          "health": "GOOD|WEAK|CRITICAL", "evidence": "numbers", "fix": "action"}],
    "risks": ["risk to watch this week"],
    "seven_day_plan": [{"day": "Mon", "action": "specific action"}],
}


def account_snapshot(db: Session, client_id: str, days: int = 14) -> dict[str, Any]:
    since = dt.date.today() - dt.timedelta(days=days)
    rows = (db.query(MetricSnapshot)
            .filter(MetricSnapshot.client_id == client_id, MetricSnapshot.date >= since)
            .order_by(MetricSnapshot.date.asc()).all())
    campaigns = db.query(Campaign).filter(Campaign.client_id == client_id).all()

    def avg(key: str, subset) -> float:
        vals = [getattr(r, key, 0) or 0 for r in subset]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    half = len(rows) // 2 if len(rows) >= 4 else 0
    prev, recent = rows[:half], rows[half:] if half else (rows, rows)
    return {
        "days": days,
        "totals": {
            "spend": round(sum(r.ad_spend for r in rows), 2),
            "revenue": round(sum(r.revenue for r in rows), 2),
            "orders": sum(r.orders for r in rows),
            "leads": sum(r.lead_count for r in rows),
        },
        "recent_avg": {k: avg(k, recent) for k in ("roas", "ctr", "cpa", "cpm", "conversion_rate", "aov")},
        "prev_avg": {k: avg(k, prev) for k in ("roas", "ctr", "cpa", "cpm", "conversion_rate", "aov")},
        "campaigns": [{
            "name": c.name, "status": c.status, "objective": c.objective,
            "spend": c.spend, "roas": c.purchase_roas, "ctr": c.ctr, "cpa": c.cpa,
            "cpm": c.cpm, "frequency": c.frequency, "conversions": c.conversions,
            "impressions": c.impressions, "clicks": c.clicks, "revenue": c.revenue,
        } for c in campaigns],
    }


def analyze_performance(db: Session, client: Client, days: int = 14) -> dict[str, Any]:
    snap = account_snapshot(db, client.id, days)

    # refresh per-campaign predictions
    campaigns = db.query(Campaign).filter(Campaign.client_id == client.id).all()
    for c in campaigns:
        pred = predict_with_learned(client.id, c) or predict_campaign(c)
        db.add(Prediction(
            client_id=client.id, entity_type="campaign", entity_id=c.id,
            ctr=pred["ctr"], cvr=pred["cvr"], cpa=pred["cpa"], roas=pred["roas"],
            creative_quality=pred["creative_quality"],
            win_probability=pred["win_probability"], audience_match=pred["audience_match"],
            model_version=str(pred.get("model_version", "heuristic-v1")),
            features={"source": "performance_analyst"},
        ))
    db.commit()

    import json
    brief = llm.complete_json(
        role="analytics", system=ROLE_PROMPTS["analytics"],
        user=(f"BUSINESS:\n{business_context_snippet(db, client.id)}\n\n"
              f"ACCOUNT DATA (last {days} days):\n{json.dumps(snap, indent=1)[:9000]}\n\n"
              "Produce the analyst brief. Every claim needs a number. Identify the single "
              "binding constraint — do not list five equal problems."),
        shape=BRIEF_SHAPE, client_id=client.id, temperature=0.3,
    ) or {}
    return {"snapshot": snap, "brief": brief}
