"""Module 4 — Creative Intelligence.

Bulk-generates ad creative assets across 13 copy frameworks and 10 asset kinds:
hooks, headlines, angles, primary texts, UGC concepts, reel concepts, image-ad
concepts, carousels, scripts, CTAs. Each asset carries its framework, target
persona, awareness level, and a predicted quality score.
"""
from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.ml.predictors import predict_creative
from app.models.aether import CreativeAsset, Persona
from app.models.models import Client
from app.modules.business_intel import business_context_snippet
from app.rag.store import build_context

log = logging.getLogger("aether.creative")

FRAMEWORKS = ["AIDA", "PAS", "BAB", "STORY", "UGC", "FOUNDER", "AUTHORITY",
              "PROBLEM", "CURIOSITY", "SHOCK", "COMPARISON", "TESTIMONIAL", "CASE_STUDY"]

KINDS = ["hook", "headline", "angle", "primary_text", "ugc_concept", "reel_concept",
         "image_concept", "carousel", "script", "cta"]

# per-kind generation instructions the Copy/Creative agents receive
KIND_SPECS: dict[str, str] = {
    "hook": ("Scroll-stopping opening lines (max 12 words each) for video or text ads. Vary the "
             "structural type across: question, bold claim, callout, negation, statistic, POV, confession."),
    "headline": "Ad headlines (max 8 words). One specific outcome each. No vague brand fluff.",
    "angle": ("Ad angles: the strategic vantage the ad attacks from (e.g. 'cost of inaction', "
              "'us-vs-them', 'new mechanism', 'identity claim'). One line each + why it works for this market."),
    "primary_text": ("Full Meta primary texts (60-150 words) following the assigned framework: "
                     "pattern-interrupt open, body with proof, single CTA. Line breaks for scannability."),
    "ugc_concept": ("UGC video briefs a creator could shoot tomorrow: scenario, setting, first line "
                    "spoken to camera, demo moment, and the 'imperfection' that keeps it native."),
    "reel_concept": ("Reels/TikTok-style concepts with beat sheet: 0-2s hook (visual + text overlay), "
                     "2-10s retention device, payoff, CTA. Name the trend/format it rides if any."),
    "image_concept": ("Static image ad concepts: composition, focal point, text overlay (exact words), "
                      "color direction, why it stops the scroll in a feed."),
    "carousel": ("Carousel narratives: 4-6 cards, exact card-by-card copy (headline per card), "
                 "and the curiosity gap that pulls users to swipe."),
    "script": ("30-45s video ad scripts: [HOOK], [PROBLEM], [MECHANISM/PROOF], [OFFER], [CTA] with "
               "spoken lines + b-roll directions."),
    "cta": "Call-to-action lines matched to awareness level (soft for cold, direct for hot).",
}

BATCH_SHAPE = {
    "assets": [{
        "content": "the creative asset text (complete, ready to use)",
        "framework": "one of the allowed frameworks",
        "angle": "the underlying angle in 3-6 words",
        "awareness_level": "unaware|problem_aware|solution_aware|product_aware|most_aware",
        "why_it_works": "one sentence on the psychology",
        "visual_direction": "visual note if applicable, else empty string",
    }],
}


def generate_creatives(db: Session, client: Client, *, kind: str, count: int = 20,
                       persona_id: str | None = None, framework: str | None = None,
                       product_hint: str = "") -> list[CreativeAsset]:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    count = max(1, min(count, 100))

    persona = db.get(Persona, persona_id) if persona_id else None
    persona_block = "(no specific persona — write for the broad ideal customer)"
    if persona:
        persona_block = (f"PERSONA: {persona.name} | awareness: {persona.awareness_level} | "
                         f"sophistication: {persona.sophistication}/5\n"
                         f"Pains: {persona.pains}\nDreams: {persona.dream_outcome}\n"
                         f"Objections: {persona.objections}\nTheir words: {persona.language}")

    biz = business_context_snippet(db, client.id)
    voc = build_context(db, client.id, f"customer language reviews pains {product_hint}",
                        namespaces=["research", "business"], k=5, max_chars=4000)
    frameworks = [framework] if framework in FRAMEWORKS else FRAMEWORKS
    role = "copy" if kind in ("hook", "headline", "primary_text", "cta", "angle") else "creative"

    batch_id = str(uuid4())
    created: list[CreativeAsset] = []
    remaining = count
    # chunk requests so long batches stay within output limits
    while remaining > 0:
        n = min(remaining, 20)
        data = llm.complete_json(
            role=role, system=ROLE_PROMPTS[role],
            user=(f"CLIENT:\n{biz}\n\n{persona_block}\n\n"
                  f"VOICE OF CUSTOMER (retrieved):\n{voc}\n\n"
                  f"Product/offer focus: {product_hint or 'core offer'}\n\n"
                  f"TASK: Generate exactly {n} {kind.replace('_', ' ')}s.\n{KIND_SPECS[kind]}\n"
                  f"Distribute across these frameworks: {frameworks}. No two assets may share "
                  "the same angle × framework combination. Ground copy in the voice-of-customer."),
            shape=BATCH_SHAPE, client_id=client.id, temperature=0.9,
        ) or {}
        assets = data.get("assets") or []
        if not assets:
            break
        for a in assets[:n]:
            content = str(a.get("content", "")).strip()
            if not content:
                continue
            fw = a.get("framework") if a.get("framework") in FRAMEWORKS else frameworks[0]
            row = CreativeAsset(
                client_id=client.id, persona_id=persona.id if persona else None,
                batch_id=batch_id, kind=kind, framework=fw, content=content,
                meta={"angle": a.get("angle"), "awareness_level": a.get("awareness_level"),
                      "why_it_works": a.get("why_it_works"),
                      "visual_direction": a.get("visual_direction")},
            )
            row.predicted_score = predict_creative(content, kind, fw)["creative_quality"]
            db.add(row)
            created.append(row)
        remaining -= n
    db.commit()
    return created


def serialize_asset(a: CreativeAsset) -> dict:
    return {
        "id": a.id, "kind": a.kind, "framework": a.framework, "content": a.content,
        "meta": a.meta or {}, "predicted_score": round(a.predicted_score, 1),
        "status": a.status, "persona_id": a.persona_id, "batch_id": a.batch_id,
        "created_at": a.created_at.isoformat(),
    }
