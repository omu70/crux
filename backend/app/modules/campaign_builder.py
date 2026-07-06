"""Module 6 — Campaign Builder.

Turns strategy + personas + creatives into a complete, launchable Meta
campaign blueprint: structure, naming convention, budget split, objectives,
placements, pixel mapping, audience strategy, creative rotation, scaling plan.
Publishing goes through services.meta_publish (always PAUSED).
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.models.aether import CampaignBlueprint, CreativeAsset, Persona
from app.models.models import Client
from app.modules.business_intel import business_context_snippet
from app.services.meta_publish import meta_publisher

log = logging.getLogger("aether.builder")

BLUEPRINT_SHAPE = {
    "campaign": {
        "name": "name following the naming convention",
        "objective": "OUTCOME_SALES|OUTCOME_LEADS|OUTCOME_TRAFFIC|OUTCOME_AWARENESS|OUTCOME_ENGAGEMENT",
        "buying_type": "AUCTION",
        "notes": "strategic role of this campaign",
    },
    "naming_convention": {"pattern": "e.g. [GEO]-[OBJ]-[AUDIENCE]-[DATE]", "rationale": "why"},
    "ad_sets": [{
        "name": "ad set name",
        "audience": "who this targets and why",
        "targeting": {"geo": ["country"], "age_range": "e.g. 25-54",
                      "interests": ["interest"], "custom_audiences": ["lookalike/retargeting note"],
                      "advantage_plus": "score"},
        "optimization_goal": "OFFSITE_CONVERSIONS|LEAD_GENERATION|LINK_CLICKS",
        "conversion_event": "PURCHASE|LEAD|ADD_TO_CART|COMPLETE_REGISTRATION",
        "placements": ["advantage_plus OR list: facebook_feed, instagram_reels, stories..."],
        "budget_share_pct": "score",
        "ads": [{
            "name": "ad name",
            "creative_asset_hint": "which kind of creative goes here (hook/angle/format)",
            "headline": "headline",
            "primary_text": "primary text",
            "cta_type": "SHOP_NOW|LEARN_MORE|SIGN_UP|GET_OFFER|BOOK_TRAVEL|CONTACT_US",
            "link": "landing page URL or placeholder",
        }],
    }],
    "budget_plan": {"daily_total": 100.0, "split_rationale": "why this split",
                    "guardrails": ["spending guardrail"]},
    "audience_strategy": {"approach": "broad|interest-stack|lookalike-ladder|retargeting-tiers",
                          "rationale": "why", "exclusions": ["audience to exclude"]},
    "pixel_mapping": {"events": [{"event": "PageView|ViewContent|AddToCart|InitiateCheckout|Purchase|Lead",
                                  "where": "where it fires", "critical": True}]},
    "creative_rotation": {"policy": "how creatives rotate", "refresh_trigger": "metric condition",
                          "max_ads_per_adset": 6},
    "scaling_plan": {
        "vertical": {"rule": "budget increase rule", "max_daily_change_pct": 20},
        "horizontal": {"rule": "duplication strategy into new audiences/geos"},
        "triggers": [{"condition": "measurable condition", "action": "what to do"}],
    },
    "rationale": "one paragraph: why this structure wins for this business",
}


def build_blueprint(db: Session, client: Client, *, goal: str, daily_budget: float,
                    persona_ids: list[str] | None = None,
                    landing_url: str = "") -> CampaignBlueprint:
    biz = business_context_snippet(db, client.id)

    personas = []
    if persona_ids:
        personas = db.query(Persona).filter(Persona.id.in_(persona_ids)).all()
    if not personas:
        personas = (db.query(Persona).filter(Persona.client_id == client.id)
                    .order_by(Persona.created_at.desc()).limit(3).all())
    persona_block = "\n\n".join(
        f"- {p.name} ({p.awareness_level}, intent {p.purchase_intent}): pains {p.pains}; "
        f"targeting {p.targeting}" for p in personas
    ) or "(no personas yet — design a broad + retargeting structure)"

    top_creatives = (db.query(CreativeAsset)
                     .filter(CreativeAsset.client_id == client.id,
                             CreativeAsset.kind.in_(["headline", "primary_text", "hook"]))
                     .order_by(CreativeAsset.predicted_score.desc()).limit(12).all())
    creative_block = "\n".join(
        f"- [{c.kind}/{c.framework} score {c.predicted_score:.0f}] {c.content[:160]}"
        for c in top_creatives
    ) or "(no creatives generated yet — write placeholder copy in the blueprint)"

    data = llm.complete_json(
        role="optimization", system=ROLE_PROMPTS["optimization"],
        user=(f"CLIENT:\n{biz}\n\nGOAL: {goal}\nDAILY BUDGET: {client.currency} {daily_budget}\n"
              f"LANDING PAGE: {landing_url or '(use site root)'}\n\n"
              f"PERSONAS:\n{persona_block}\n\n"
              f"BEST AVAILABLE CREATIVES (use these in the ads):\n{creative_block}\n\n"
              "Design the complete Meta campaign blueprint. 2-4 ad sets, 2-4 ads each. "
              "Budget shares must sum to 100. Structure must exit learning phase fast "
              "(consolidated, not fragmented)."),
        shape=BLUEPRINT_SHAPE, client_id=client.id, temperature=0.4,
    ) or {}

    camp = data.get("campaign", {})
    bp = CampaignBlueprint(
        client_id=client.id,
        name=camp.get("name", f"Aether — {goal[:60]}"),
        objective=camp.get("objective", "OUTCOME_SALES"),
        status="READY",
        daily_budget=daily_budget,
        structure={"campaign": camp, "ad_sets": data.get("ad_sets", [])},
        naming=data.get("naming_convention"),
        budget_plan=data.get("budget_plan"),
        audience_strategy=data.get("audience_strategy"),
        placements={"per_ad_set": [a.get("placements") for a in data.get("ad_sets", [])]},
        pixel_mapping=data.get("pixel_mapping"),
        creative_rotation=data.get("creative_rotation"),
        scaling_plan=data.get("scaling_plan"),
        rationale=data.get("rationale"),
    )
    db.add(bp)
    db.commit()
    return bp


def publish_blueprint(db: Session, client: Client, bp: CampaignBlueprint) -> dict:
    bp.status = "PUBLISHING"
    db.commit()
    try:
        result = meta_publisher.publish_blueprint(
            bp.name, bp.structure or {}, bp.daily_budget, currency=client.currency,
        )
        bp.published_ids = result
        bp.status = "PUBLISHED"
        db.commit()
        return result
    except Exception as exc:
        bp.status = "FAILED"
        db.commit()
        log.exception("blueprint publish failed")
        raise


def serialize_blueprint(bp: CampaignBlueprint) -> dict:
    return {
        "id": bp.id, "name": bp.name, "objective": bp.objective, "status": bp.status,
        "daily_budget": bp.daily_budget, "structure": bp.structure or {},
        "naming": bp.naming, "budget_plan": bp.budget_plan,
        "audience_strategy": bp.audience_strategy, "placements": bp.placements,
        "pixel_mapping": bp.pixel_mapping, "creative_rotation": bp.creative_rotation,
        "scaling_plan": bp.scaling_plan, "published_ids": bp.published_ids,
        "rationale": bp.rationale,
        "created_at": bp.created_at.isoformat(), "updated_at": bp.updated_at.isoformat(),
    }
