"""8-dimension campaign scoring engine.

Every campaign (live or blueprint) gets: Overall, Creative, Audience, Offer,
Landing Page, Tracking, Brand, Scaling — each 0-100 with reasons and fixes.
Quantitative dimensions come from metrics; qualitative ones from the
Analytics agent grading against the business profile.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.ml.predictors import predict_campaign
from app.models.aether import CampaignScore
from app.models.models import Campaign, Client, Integration
from app.modules.business_intel import business_context_snippet

log = logging.getLogger("aether.scoring")

WEIGHTS = {"creative": 0.20, "audience": 0.15, "offer": 0.20, "landing_page": 0.15,
           "tracking": 0.10, "brand": 0.08, "scaling": 0.12}

QUAL_SHAPE = {
    "offer": {"score": "score", "reason": "why", "fix": "highest-leverage fix"},
    "landing_page": {"score": "score", "reason": "why", "fix": "highest-leverage fix"},
    "brand": {"score": "score", "reason": "why", "fix": "highest-leverage fix"},
}


def _creative_score(c: Campaign) -> tuple[int, str]:
    ctr = c.ctr or 0
    if ctr >= 2.0:
        return min(95, int(60 + ctr * 12)), f"CTR {ctr:.2f}% is well above the ~1.2% feed benchmark"
    if ctr >= 1.0:
        return int(55 + (ctr - 1.0) * 20), f"CTR {ctr:.2f}% is around benchmark"
    return max(15, int(ctr * 45)), f"CTR {ctr:.2f}% is below benchmark — creative is the likely constraint"


def _audience_score(c: Campaign) -> tuple[int, str]:
    freq = c.frequency or 0
    base = 70
    if freq > 4:
        base -= int((freq - 4) * 12)
        reason = f"Frequency {freq:.1f} signals audience saturation"
    elif freq > 2.5:
        base -= int((freq - 2.5) * 6)
        reason = f"Frequency {freq:.1f} is creeping up — expand or refresh soon"
    else:
        reason = f"Frequency {freq:.1f} is healthy"
    if (c.conversions or 0) < 10 and (c.spend or 0) > 0:
        base -= 10
        reason += "; low conversion volume weakens delivery optimization"
    return max(5, min(95, base)), reason


def _tracking_score(db: Session, client_id: str) -> tuple[int, str]:
    kinds = {i.type: i.status for i in
             db.query(Integration).filter(Integration.client_id == client_id).all()}
    score, notes = 30, []
    if kinds.get("META_ADS") == "CONNECTED":
        score += 30
        notes.append("Meta connected")
    if kinds.get("GA4") == "CONNECTED":
        score += 15
        notes.append("GA4 connected")
    if kinds.get("SHOPIFY") == "CONNECTED" or kinds.get("WOOCOMMERCE") == "CONNECTED":
        score += 25
        notes.append("commerce platform connected (revenue truth-source)")
    return min(100, score), "; ".join(notes) or "no integrations connected"


def _scaling_score(c: Campaign) -> tuple[int, str]:
    p = predict_campaign(c)
    win, roas = p["win_probability"], p["roas"]
    if win > 0.65 and roas >= 2.5:
        return int(70 + win * 25), f"Win probability {win:.0%} at ROAS {roas:.1f}x — clear scaling headroom"
    if win > 0.5:
        return int(45 + win * 30), f"Win probability {win:.0%} — scale cautiously (≤20%/day)"
    return max(10, int(win * 60)), f"Win probability {win:.0%} — fix efficiency before scaling"


def score_campaign(db: Session, client: Client, campaign: Campaign) -> CampaignScore:
    creative, creative_r = _creative_score(campaign)
    audience, audience_r = _audience_score(campaign)
    tracking, tracking_r = _tracking_score(db, client.id)
    scaling, scaling_r = _scaling_score(campaign)

    qual = llm.complete_json(
        role="analytics", system=ROLE_PROMPTS["analytics"],
        user=(f"BUSINESS:\n{business_context_snippet(db, client.id)}\n\n"
              f"CAMPAIGN: {campaign.name} | objective {campaign.objective} | "
              f"spend {campaign.spend} | ROAS {campaign.purchase_roas} | CTR {campaign.ctr}% | "
              f"CPA {campaign.cpa} | conversions {campaign.conversions} | freq {campaign.frequency}\n\n"
              "Grade the OFFER strength, LANDING PAGE (infer from conversion efficiency: "
              "clicks vs conversions), and BRAND consistency of this campaign, 0-100 each."),
        shape=QUAL_SHAPE, client_id=client.id, temperature=0.3,
    ) or {}

    def q(dim: str) -> tuple[int, str, str]:
        d = qual.get(dim) or {}
        try:
            s = max(0, min(100, int(d.get("score", 55))))
        except (TypeError, ValueError):
            s = 55
        return s, str(d.get("reason", "")), str(d.get("fix", ""))

    offer, offer_r, offer_fix = q("offer")
    lp, lp_r, lp_fix = q("landing_page")
    brand, brand_r, brand_fix = q("brand")

    dims = {"creative": creative, "audience": audience, "offer": offer,
            "landing_page": lp, "tracking": tracking, "brand": brand, "scaling": scaling}
    overall = round(sum(dims[k] * w for k, w in WEIGHTS.items()))

    row = CampaignScore(
        client_id=client.id, campaign_id=campaign.id, date=dt.date.today(),
        overall=overall, creative=creative, audience=audience, offer=offer,
        landing_page=lp, tracking=tracking, brand=brand, scaling=scaling,
        details={
            "creative": {"reason": creative_r},
            "audience": {"reason": audience_r},
            "offer": {"reason": offer_r, "fix": offer_fix},
            "landing_page": {"reason": lp_r, "fix": lp_fix},
            "tracking": {"reason": tracking_r},
            "brand": {"reason": brand_r, "fix": brand_fix},
            "scaling": {"reason": scaling_r},
            "weights": WEIGHTS,
        },
    )
    db.add(row)
    db.commit()
    return row


def serialize_score(s: CampaignScore) -> dict[str, Any]:
    return {
        "id": s.id, "campaign_id": s.campaign_id, "blueprint_id": s.blueprint_id,
        "date": s.date.isoformat(), "overall": s.overall,
        "dimensions": {
            "creative": s.creative, "audience": s.audience, "offer": s.offer,
            "landing_page": s.landing_page, "tracking": s.tracking,
            "brand": s.brand, "scaling": s.scaling,
        },
        "details": s.details or {},
    }
