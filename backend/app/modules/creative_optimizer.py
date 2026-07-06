"""Module 8 — Creative Optimization AI.

Detects creative / audience / offer / ad fatigue from metric trends and
auto-generates replacement creatives for fatigued assets.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.aether import FatigueSignal
from app.models.models import Campaign, Client, MetricSnapshot
from app.modules.creative_intel import generate_creatives

log = logging.getLogger("aether.fatigue")


def _trend(values: list[float]) -> float:
    """Simple slope of a series normalized by its mean (pct/day-ish)."""
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n < 4:
        return 0.0
    mean = sum(vals) / n or 1.0
    xbar = (n - 1) / 2
    num = sum((i - xbar) * (v - mean) for i, v in enumerate(vals))
    den = sum((i - xbar) ** 2 for i in range(n)) or 1.0
    return (num / den) / abs(mean)


def detect_fatigue(db: Session, client: Client, days: int = 14) -> list[FatigueSignal]:
    """Rule-based fatigue detection over campaigns + account trend."""
    signals: list[FatigueSignal] = []
    since = dt.date.today() - dt.timedelta(days=days)
    rows = (db.query(MetricSnapshot)
            .filter(MetricSnapshot.client_id == client.id, MetricSnapshot.date >= since)
            .order_by(MetricSnapshot.date.asc()).all())
    campaigns = db.query(Campaign).filter(Campaign.client_id == client.id,
                                          Campaign.status == "ACTIVE").all()

    ctr_trend = _trend([r.ctr for r in rows])
    cpa_trend = _trend([r.cpa for r in rows])

    def add(entity_type: str, ref: str, ftype: str, severity: str,
            evidence: dict[str, Any], rec: str) -> None:
        # dedupe unresolved identical signals
        exists = (db.query(FatigueSignal)
                  .filter(FatigueSignal.client_id == client.id,
                          FatigueSignal.entity_ref == ref,
                          FatigueSignal.fatigue_type == ftype,
                          FatigueSignal.resolved.is_(False)).first())
        if exists:
            return
        sig = FatigueSignal(client_id=client.id, entity_type=entity_type, entity_ref=ref,
                            fatigue_type=ftype, severity=severity, evidence=evidence,
                            recommendation=rec)
        db.add(sig)
        signals.append(sig)

    # account-level creative fatigue
    if ctr_trend < -0.03:
        add("campaign", "account", "creative",
            "CRITICAL" if ctr_trend < -0.06 else "WARNING",
            {"ctr_trend_per_day": round(ctr_trend, 4), "window_days": days},
            "Account CTR is decaying — refresh top-of-funnel creative batch this week.")

    # offer fatigue: CPA rising while CTR stable
    if cpa_trend > 0.03 and abs(ctr_trend) < 0.02:
        add("campaign", "account", "offer", "WARNING",
            {"cpa_trend_per_day": round(cpa_trend, 4), "ctr_trend_per_day": round(ctr_trend, 4)},
            "CPA rising with stable CTR — the ad still stops people but the offer/LP converts worse. "
            "Test a stronger offer (bundle, risk-reversal, urgency) before touching creative.")

    for c in campaigns:
        freq = c.frequency or 0
        if freq >= 4.0:
            add("campaign", c.name, "audience", "CRITICAL",
                {"frequency": freq},
                f"Frequency {freq:.1f} — audience is saturated. Expand targeting or duplicate "
                "into a fresh audience; expect CPM relief within 3-5 days.")
        elif freq >= 3.0:
            add("campaign", c.name, "audience", "WARNING",
                {"frequency": freq},
                f"Frequency {freq:.1f} — schedule creative refresh before performance decays.")
        if (c.ctr or 0) < 0.7 and (c.spend or 0) > 0 and (c.impressions or 0) > 5000:
            add("campaign", c.name, "ad", "WARNING",
                {"ctr": c.ctr, "impressions": c.impressions},
                f"CTR {c.ctr:.2f}% after {c.impressions} impressions — hooks are not stopping "
                "the scroll. Rotate in new hook variants.")

    db.commit()
    return signals


def auto_refresh_creatives(db: Session, client: Client,
                           signal: FatigueSignal, count: int = 10) -> dict[str, Any]:
    """Generate replacement creatives targeted at the fatigue type."""
    kind_by_fatigue = {"creative": "hook", "ad": "hook", "offer": "primary_text", "audience": "angle"}
    kind = kind_by_fatigue.get(signal.fatigue_type, "hook")
    assets = generate_creatives(
        db, client, kind=kind, count=count,
        product_hint=f"Replacements for fatigued {signal.entity_ref}: {signal.recommendation}",
    )
    signal.resolved = True
    db.commit()
    return {"generated": len(assets), "kind": kind, "signal_id": signal.id,
            "asset_ids": [a.id for a in assets]}


def serialize_signal(s: FatigueSignal) -> dict:
    return {
        "id": s.id, "entity_type": s.entity_type, "entity_ref": s.entity_ref,
        "fatigue_type": s.fatigue_type, "severity": s.severity,
        "evidence": s.evidence or {}, "recommendation": s.recommendation,
        "resolved": s.resolved, "created_at": s.created_at.isoformat(),
    }
