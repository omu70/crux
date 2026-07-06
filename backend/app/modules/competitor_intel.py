"""Module 2 — Competitor Intelligence.

discover_competitors: AI proposes the top competitors from the business profile.
analyze_competitor:   fetches the competitor's site and builds a full profile
                      (pricing, offers, angles, funnels, SWOT, positioning gap).
"""
from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.models.aether import CompetitorProfile
from app.models.models import Client
from app.modules.business_intel import business_context_snippet
from app.rag.ingest import fetch_page_text, ingest_text

log = logging.getLogger("aether.competitors")

DISCOVERY_SHAPE = {
    "competitors": [{
        "name": "competitor brand name",
        "website": "https://...",
        "why_competitor": "why they compete for the same customer",
        "threat_level": "LOW|MEDIUM|HIGH",
    }],
}

PROFILE_SHAPE = {
    "pricing": {"model": "how they charge", "points": ["visible price point"], "vs_client": "cheaper|similar|premium"},
    "offers": [{"name": "offer", "promise": "the promise it leads with", "hook": "how it's framed"}],
    "creative_angles": ["advertising angle they visibly use"],
    "headlines": ["actual or representative headline from their site/ads"],
    "funnels": [{"entry": "entry point", "steps": ["step"], "monetization": "how it converts"}],
    "reviews_summary": {"positives": ["what customers praise"], "negatives": ["what customers complain about"],
                        "themes": ["recurring theme"]},
    "ads": {"strategy": "their visible paid-social strategy", "formats": ["format they favor"],
            "estimated_intensity": "LOW|MEDIUM|HIGH"},
    "seo": {"keywords": ["keyword they target"], "content_focus": "their content strategy focus"},
    "content_strategy": ["observable content play"],
    "email_funnels": ["visible email capture / flow"],
    "swot": {"strengths": ["strength"], "weaknesses": ["weakness"],
             "opportunities": ["opportunity for the CLIENT"], "threats": ["threat to the CLIENT"]},
    "positioning_gap": "the clearest way the client can position AGAINST this competitor",
}


def discover_competitors(db: Session, client: Client, *, count: int = 5,
                         industry_hint: str = "") -> list[CompetitorProfile]:
    biz = business_context_snippet(db, client.id)
    data = llm.complete_json(
        role="research", system=ROLE_PROMPTS["research"],
        user=(f"Client business:\n{biz}\n\nIndustry hint: {industry_hint or '(none)'}\n\n"
              f"Identify the top {count} direct competitors this business fights for customers "
              "with. Prefer competitors an ad buyer would actually see in the auction. "
              "Real brands where you know them; plausible archetypes labelled '(archetype)' where you don't."),
        shape=DISCOVERY_SHAPE, client_id=client.id, temperature=0.5,
    ) or {}
    created: list[CompetitorProfile] = []
    existing = {c.name.lower() for c in
                db.query(CompetitorProfile).filter(CompetitorProfile.client_id == client.id).all()}
    for comp in (data.get("competitors") or [])[:count]:
        name = str(comp.get("name", "")).strip()
        if not name or name.lower() in existing:
            continue
        row = CompetitorProfile(
            client_id=client.id, name=name[:200], website=comp.get("website"),
            discovered_via="ai", threat_level=comp.get("threat_level", "MEDIUM"),
            swot={"why_competitor": comp.get("why_competitor")},
        )
        db.add(row)
        created.append(row)
    db.commit()
    return created


def analyze_competitor(db: Session, client: Client, competitor: CompetitorProfile) -> CompetitorProfile:
    site_text = ""
    if competitor.website:
        try:
            site_text = fetch_page_text(competitor.website)[:15000]
        except Exception as exc:
            log.warning("competitor site fetch failed (%s): %s", competitor.website, exc)

    biz = business_context_snippet(db, client.id)
    data = llm.complete_json(
        role="research", system=ROLE_PROMPTS["research"],
        user=(f"CLIENT (whom we serve):\n{biz}\n\n"
              f"COMPETITOR: {competitor.name} ({competitor.website or 'no site'})\n"
              f"COMPETITOR SITE CONTENT:\n{site_text or '(unavailable — infer carefully, mark inferences)'}\n\n"
              "Build the full competitor intelligence profile from the client's perspective."),
        shape=PROFILE_SHAPE, client_id=client.id, temperature=0.4,
    ) or {}

    for field in ("pricing", "offers", "creative_angles", "headlines", "funnels",
                  "reviews_summary", "ads", "seo", "content_strategy", "email_funnels", "swot"):
        if data.get(field) is not None:
            setattr(competitor, field, data[field])
    competitor.positioning_gap = data.get("positioning_gap")
    competitor.last_analyzed_at = dt.datetime.now(dt.timezone.utc)
    db.commit()

    try:
        ingest_text(db, client.id, f"Competitor profile: {competitor.name}",
                    f"Angles: {competitor.creative_angles}\nHeadlines: {competitor.headlines}\n"
                    f"SWOT: {competitor.swot}\nGap: {competitor.positioning_gap}",
                    namespace="research", source_type="manual")
    except Exception:
        log.debug("competitor self-ingest skipped", exc_info=True)
    return competitor


def serialize_competitor(c: CompetitorProfile) -> dict:
    return {
        "id": c.id, "name": c.name, "website": c.website,
        "discovered_via": c.discovered_via, "threat_level": c.threat_level,
        "pricing": c.pricing, "offers": c.offers or [],
        "creative_angles": c.creative_angles or [], "headlines": c.headlines or [],
        "funnels": c.funnels or [], "reviews_summary": c.reviews_summary,
        "ads": c.ads, "seo": c.seo, "content_strategy": c.content_strategy or [],
        "email_funnels": c.email_funnels or [], "swot": c.swot,
        "positioning_gap": c.positioning_gap,
        "last_analyzed_at": c.last_analyzed_at.isoformat() if c.last_analyzed_at else None,
        "created_at": c.created_at.isoformat(),
    }
