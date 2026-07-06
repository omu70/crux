"""Module 9 — Budget Optimizer.

Rule engine + Optimization agent produce concrete actions per campaign:
increase / decrease / duplicate / kill / scale vertical / scale horizontal /
budget split. Actions are PROPOSED; applying one calls the Meta publisher
(mock-safe) and marks it APPLIED.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.ml.predictors import predict_campaign
from app.models.aether import OptimizationAction
from app.models.models import Campaign, Client
from app.services.meta_publish import meta_publisher

log = logging.getLogger("aether.budget")

REVIEW_SHAPE = {
    "actions": [{
        "campaign": "campaign name",
        "action": "increase_budget|decrease_budget|duplicate|kill|scale_vertical|scale_horizontal|budget_split|refresh_creative",
        "magnitude_pct": "score",
        "reason": "numbers-backed reason",
        "trigger_condition": "what made this fire now",
        "rollback": "condition to revert",
        "confidence": "confidence",
        "expected_impact": "quantified expectation",
    }],
}


def _rule_actions(campaigns: list[Campaign], target_roas: float) -> list[dict[str, Any]]:
    out = []
    for c in campaigns:
        if c.status != "ACTIVE":
            continue
        p = predict_campaign(c)
        roas, win, freq = (c.purchase_roas or 0), p["win_probability"], (c.frequency or 0)
        conv = c.conversions or 0
        if conv < 10 and (c.spend or 0) < 100:
            continue  # learning — leave alone
        if roas >= max(target_roas * 1.3, 3.0) and win >= 0.6:
            out.append({"campaign": c.name, "action": "increase_budget", "magnitude_pct": 20,
                        "reason": f"ROAS {roas:.1f}x ≥ 1.3× target with win-prob {win:.0%}",
                        "confidence": round(win, 2),
                        "expected_impact": "≈15-20% more volume at similar efficiency"})
            if freq < 2.5:
                out.append({"campaign": c.name, "action": "scale_horizontal", "magnitude_pct": 100,
                            "reason": f"Winner with low frequency ({freq:.1f}) — headroom in new audiences",
                            "confidence": round(win * 0.85, 2),
                            "expected_impact": "duplicate into 1-2 fresh audiences at 50% of source budget"})
        elif roas < target_roas * 0.5 and conv >= 10:
            out.append({"campaign": c.name, "action": "kill", "magnitude_pct": 100,
                        "reason": f"ROAS {roas:.1f}x < 50% of target after {conv} conversions",
                        "confidence": 0.8,
                        "expected_impact": f"reallocates {c.spend and round(c.spend, 0)} spend to winners"})
        elif roas < target_roas * 0.85:
            out.append({"campaign": c.name, "action": "decrease_budget", "magnitude_pct": 25,
                        "reason": f"ROAS {roas:.1f}x below target {target_roas:.1f}x — de-risk while iterating",
                        "confidence": 0.65,
                        "expected_impact": "protects efficiency while creative/offer fixes land"})
    return out


def run_budget_review(db: Session, client: Client) -> list[OptimizationAction]:
    campaigns = db.query(Campaign).filter(Campaign.client_id == client.id).all()
    target_roas = client.monthly_target_roas or 2.0
    rules = _rule_actions(campaigns, target_roas)

    import json
    camp_data = [{"name": c.name, "status": c.status, "spend": c.spend,
                  "roas": c.purchase_roas, "ctr": c.ctr, "cpa": c.cpa,
                  "frequency": c.frequency, "conversions": c.conversions} for c in campaigns]
    reviewed = llm.complete_json(
        role="optimization", system=ROLE_PROMPTS["optimization"],
        user=(f"Target ROAS: {target_roas}. Currency: {client.currency}.\n\n"
              f"CAMPAIGNS:\n{json.dumps(camp_data, indent=1)[:6000]}\n\n"
              f"RULE-ENGINE DRAFT ACTIONS:\n{json.dumps(rules, indent=1)[:4000]}\n\n"
              "Review, correct, drop or add actions. Respect learning phase. Final list only."),
        shape=REVIEW_SHAPE, client_id=client.id, temperature=0.3,
    ) or {}

    final = reviewed.get("actions") or rules
    by_name = {c.name: c for c in campaigns}
    created: list[OptimizationAction] = []
    valid_actions = {"increase_budget", "decrease_budget", "duplicate", "kill",
                     "scale_vertical", "scale_horizontal", "budget_split", "refresh_creative"}
    # If the LLM's review produced nothing usable, trust the rule engine.
    if not any(a.get("action") in valid_actions for a in final):
        final = rules
    for a in final[:20]:
        action = a.get("action")
        if action not in valid_actions:
            continue
        camp = by_name.get(a.get("campaign", ""))
        try:
            conf = float(a.get("confidence", 0.5))
        except (TypeError, ValueError):
            conf = 0.5
        row = OptimizationAction(
            client_id=client.id,
            campaign_id=camp.id if camp else None,
            campaign_ref=str(a.get("campaign", "unknown"))[:240],
            action=action,
            amount={"magnitude_pct": a.get("magnitude_pct"),
                    "trigger": a.get("trigger_condition"), "rollback": a.get("rollback")},
            reason=str(a.get("reason", ""))[:2000],
            confidence=max(0.0, min(1.0, conf)),
            expected_impact=str(a.get("expected_impact", ""))[:300],
        )
        db.add(row)
        created.append(row)
    db.commit()
    return created


def apply_action(db: Session, client: Client, action: OptimizationAction) -> dict[str, Any]:
    """Execute an approved action against Meta (mock-safe)."""
    result: dict[str, Any] = {"action": action.action}
    camp = db.get(Campaign, action.campaign_id) if action.campaign_id else None
    external = (camp.external_id if camp and camp.external_id else f"mock_{action.campaign_ref[:12]}")
    pct = 0
    try:
        pct = float((action.amount or {}).get("magnitude_pct") or 0)
    except (TypeError, ValueError):
        pct = 0

    if action.action in ("increase_budget", "scale_vertical"):
        result["meta"] = meta_publisher.update_budget(external, 1 + pct / 100)
    elif action.action == "decrease_budget":
        result["meta"] = meta_publisher.update_budget(external, max(0.1, 1 - pct / 100))
    elif action.action == "kill":
        result["meta"] = meta_publisher.pause(external)
        if camp:
            camp.status = "PAUSED"
    else:
        result["meta"] = {"mode": "manual", "note": f"{action.action} requires structure changes — "
                          "generated as a task for the media buyer / campaign builder."}

    action.status = "APPLIED"
    action.applied_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return result


def serialize_action(a: OptimizationAction) -> dict:
    return {
        "id": a.id, "campaign_ref": a.campaign_ref, "campaign_id": a.campaign_id,
        "action": a.action, "amount": a.amount or {}, "reason": a.reason,
        "confidence": a.confidence, "expected_impact": a.expected_impact,
        "status": a.status, "applied_at": a.applied_at.isoformat() if a.applied_at else None,
        "created_at": a.created_at.isoformat(),
    }
