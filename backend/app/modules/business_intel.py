"""Module 1 — Business Intelligence Engine.

Input: website / landing pages / Shopify / CSV / PDF / brand docs / socials.
Pipeline: ingest sources → RAG store (namespace "business"/"brand") →
Research + Strategy agents produce the full business profile.
"""
from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.models.aether import BusinessProfile
from app.models.models import Client, Product
from app.rag.ingest import fetch_page_text, ingest_text, ingest_url
from app.rag.store import build_context

log = logging.getLogger("aether.business")

PROFILE_SHAPE = {
    "summary": "3-5 sentence plain-language description of what this business sells, to whom, and how it makes money",
    "usp": "the single sharpest differentiator, stated as a customer benefit",
    "positioning": "positioning statement: for WHO, brand is the ONLY X that Y, because Z",
    "brand_voice": "tone + style description with 3 example phrases in-voice",
    "visual_style": "colors, imagery style, design mood inferred from the site",
    "offers": [{"name": "offer name", "price": "price or range", "type": "core|entry|upsell|subscription",
                "angle": "the promise this offer leads with"}],
    "price_analysis": {"tier": "budget|mid|premium|luxury",
                       "vs_market": "how pricing compares to the visible market",
                       "opportunities": ["pricing/packaging opportunity"]},
    "strengths": ["specific strength with why it matters for ads"],
    "weaknesses": ["specific weakness and its likely funnel impact"],
    "customer_journey": [{"stage": "awareness|consideration|purchase|retention",
                          "touchpoint": "what the customer experiences", "friction": "what could lose them here"}],
    "sales_funnel": [{"step": "funnel step", "purpose": "job of this step", "leak_risk": "why users drop here"}],
    "pain_points": ["customer pain this business solves"],
    "desires": [{"desire": "underlying desire", "intensity": "score", "evidence": "where this shows up"}],
    "ideal_customers": [{"label": "short persona label", "description": "who they are and why they buy"}],
}


def analyze_business(db: Session, client: Client, *, website_url: str | None = None,
                     extra_text: str | None = None, social_urls: list[str] | None = None) -> BusinessProfile:
    """Ingest sources and produce/update the client's business profile."""
    profile = (db.query(BusinessProfile)
               .filter(BusinessProfile.client_id == client.id)
               .order_by(BusinessProfile.created_at.desc()).first())
    if profile is None:
        profile = BusinessProfile(client_id=client.id)
        db.add(profile)
    profile.website_url = website_url or profile.website_url
    profile.status = "ANALYZING"
    profile.inputs = {
        "website": website_url, "socials": social_urls or [],
        "extra_text": bool(extra_text),
        "requested_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    db.commit()

    # 1 — ingest sources into the knowledge base
    site_text = ""
    if website_url:
        try:
            ingest_url(db, client.id, website_url, namespace="business", title=f"Website: {website_url}")
            site_text = fetch_page_text(website_url)[:15000]
        except Exception as exc:
            log.warning("website fetch failed: %s", exc)
    if extra_text:
        ingest_text(db, client.id, "Uploaded business notes", extra_text, namespace="business")
    for url in (social_urls or [])[:5]:
        try:
            ingest_url(db, client.id, url, namespace="business", title=f"Social: {url}")
        except Exception as exc:
            log.warning("social fetch failed for %s: %s", url, exc)

    # products already synced from Shopify/Woo enrich the picture
    products = db.query(Product).filter(Product.client_id == client.id).limit(30).all()
    product_lines = "\n".join(
        f"- {p.title} | {client.currency} {p.price} | category {p.category} | {p.units_sold} sold"
        for p in products
    )

    # 2 — retrieve + analyze
    rag = build_context(db, client.id, "business model offers customers positioning",
                        namespaces=["business", "brand"], k=8)
    task = (
        f"Company: {client.company_name}\nWebsite: {website_url or 'not provided'}\n\n"
        f"WEBSITE CONTENT (fresh fetch):\n{site_text or '(unavailable)'}\n\n"
        f"KNOWLEDGE BASE:\n{rag}\n\n"
        f"PRODUCT CATALOG:\n{product_lines or '(no synced products)'}\n\n"
        f"EXTRA NOTES:\n{(extra_text or '')[:4000]}\n\n"
        "Produce the complete business intelligence profile. Be specific to THIS business — "
        "no generic filler. Where the sources don't say something, infer carefully and mark "
        "the inference in-line with '(inferred)'."
    )
    result = llm.complete(role="strategy", system=ROLE_PROMPTS["strategy"], user=task,
                          shape=PROFILE_SHAPE, client_id=client.id, temperature=0.4)
    data = result.data or {}

    # 3 — persist
    for field in ("summary", "usp", "positioning", "brand_voice", "visual_style"):
        setattr(profile, field, data.get(field))
    profile.offers = data.get("offers")
    profile.price_analysis = data.get("price_analysis")
    profile.strengths = data.get("strengths")
    profile.weaknesses = data.get("weaknesses")
    profile.customer_journey = data.get("customer_journey")
    profile.sales_funnel = data.get("sales_funnel")
    profile.pain_points = data.get("pain_points")
    profile.desires = data.get("desires")
    profile.ideal_customers = data.get("ideal_customers")
    profile.raw = {"provider": result.provider, "model": result.model, "output": data}
    profile.status = "READY"
    db.commit()

    # 4 — store the profile itself as retrievable knowledge
    try:
        ingest_text(db, client.id, "Business profile (Aether analysis)",
                    f"Summary: {profile.summary}\nUSP: {profile.usp}\nPositioning: {profile.positioning}\n"
                    f"Voice: {profile.brand_voice}\nPains: {profile.pain_points}\nDesires: {profile.desires}",
                    namespace="business", source_type="manual")
    except Exception:
        log.debug("profile self-ingest skipped", exc_info=True)
    return profile


def serialize_profile(p: BusinessProfile) -> dict:
    return {
        "id": p.id, "status": p.status, "website_url": p.website_url,
        "summary": p.summary, "usp": p.usp, "positioning": p.positioning,
        "brand_voice": p.brand_voice, "visual_style": p.visual_style,
        "offers": p.offers or [], "price_analysis": p.price_analysis or {},
        "strengths": p.strengths or [], "weaknesses": p.weaknesses or [],
        "customer_journey": p.customer_journey or [], "sales_funnel": p.sales_funnel or [],
        "pain_points": p.pain_points or [], "desires": p.desires or [],
        "ideal_customers": p.ideal_customers or [],
        "created_at": p.created_at.isoformat(), "updated_at": p.updated_at.isoformat(),
    }


def business_context_snippet(db: Session, client_id: str, max_chars: int = 2500) -> str:
    """Compact business context reused by every other module's prompts."""
    p = (db.query(BusinessProfile).filter(BusinessProfile.client_id == client_id)
         .order_by(BusinessProfile.created_at.desc()).first())
    if not p or p.status != "READY":
        return "(business profile not yet generated)"
    text = (f"Business: {p.summary}\nUSP: {p.usp}\nPositioning: {p.positioning}\n"
            f"Brand voice: {p.brand_voice}\nKey pains solved: {p.pain_points}\n"
            f"Offers: {p.offers}")
    return text[:max_chars]
