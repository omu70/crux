"""Module 3 — Audience Intelligence Engine.

Generates deep buyer personas: pains, fears, dream outcomes, objections,
buying triggers, identity, lifestyle, verbatim language, JTBD, awareness level
(Schwartz), market sophistication, and a Meta targeting suggestion per persona.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.models.aether import Persona
from app.models.models import Client
from app.modules.business_intel import business_context_snippet
from app.rag.store import build_context

log = logging.getLogger("aether.audience")

PERSONAS_SHAPE = {
    "market_sophistication": "score",  # 1-5 Schwartz stage for the market overall
    "market_notes": "one paragraph: where this market sits and what that means for messaging",
    "personas": [{
        "name": "alliterative memorable name, e.g. 'Overwhelmed Ops Olivia'",
        "segment": "segment label",
        "awareness_level": "unaware|problem_aware|solution_aware|product_aware|most_aware",
        "sophistication": "score",
        "purchase_intent": "LOW|MEDIUM|HIGH",
        "pains": ["specific pain in their words"],
        "fears": ["fear that blocks purchase"],
        "dream_outcome": ["what life looks like after the product works"],
        "objections": [{"objection": "objection", "rebuttal": "the honest counter"}],
        "buying_triggers": ["event/moment that flips them from browsing to buying"],
        "identity": {"self_image": "how they see themselves", "aspiration": "who they want to be",
                     "tribe": "who they signal belonging to"},
        "lifestyle": ["lifestyle detail that shapes buying"],
        "language": ["verbatim phrase they would actually type/say"],
        "behavior": {"channels": ["where they hang out"], "content": ["content they consume"],
                     "buying_habits": "how they research and buy"},
        "jobs_to_be_done": [{"job": "job", "context": "when it arises", "outcome": "success measure"}],
        "emotional_triggers": ["emotion that moves them to act"],
        "targeting": {"interests": ["Meta interest"], "behaviors": ["Meta behavior"],
                      "age_range": "e.g. 28-45", "notes": "targeting strategy note"},
    }],
}


def generate_personas(db: Session, client: Client, *, count: int = 4,
                      focus: str = "") -> tuple[list[Persona], dict]:
    biz = business_context_snippet(db, client.id)
    research = build_context(db, client.id, "customer pains desires objections reviews language",
                             namespaces=["research", "business"], k=8)
    data = llm.complete_json(
        role="research", system=ROLE_PROMPTS["research"],
        user=(f"CLIENT BUSINESS:\n{biz}\n\nRESEARCH & VOICE-OF-CUSTOMER ON FILE:\n{research}\n\n"
              f"Focus: {focus or 'full market'}\n\n"
              f"Generate {count} buyer personas for paid social. Ground every field in the "
              "research where possible; language fields must sound like real customers, not "
              "marketers. Spread personas across different awareness levels."),
        shape=PERSONAS_SHAPE, client_id=client.id, temperature=0.6,
    ) or {}

    created: list[Persona] = []
    for p in (data.get("personas") or [])[:count]:
        try:
            soph = int(p.get("sophistication", 3))
        except (TypeError, ValueError):
            soph = 3
        awareness = p.get("awareness_level", "problem_aware")
        if awareness not in ("unaware", "problem_aware", "solution_aware",
                             "product_aware", "most_aware"):
            awareness = "problem_aware"
        row = Persona(
            client_id=client.id,
            name=str(p.get("name", "Unnamed Persona"))[:160],
            segment=str(p.get("segment", ""))[:160] or None,
            awareness_level=awareness,
            sophistication=max(1, min(5, soph)),
            purchase_intent=p.get("purchase_intent", "MEDIUM"),
            pains=p.get("pains"), fears=p.get("fears"), dream_outcome=p.get("dream_outcome"),
            objections=p.get("objections"), buying_triggers=p.get("buying_triggers"),
            identity=p.get("identity"), lifestyle=p.get("lifestyle"), language=p.get("language"),
            behavior=p.get("behavior"), jobs_to_be_done=p.get("jobs_to_be_done"),
            emotional_triggers=p.get("emotional_triggers"), targeting=p.get("targeting"),
        )
        db.add(row)
        created.append(row)
    db.commit()

    market = {"market_sophistication": data.get("market_sophistication"),
              "market_notes": data.get("market_notes")}
    return created, market


def serialize_persona(p: Persona) -> dict:
    return {
        "id": p.id, "name": p.name, "segment": p.segment,
        "awareness_level": p.awareness_level, "sophistication": p.sophistication,
        "purchase_intent": p.purchase_intent,
        "pains": p.pains or [], "fears": p.fears or [], "dream_outcome": p.dream_outcome or [],
        "objections": p.objections or [], "buying_triggers": p.buying_triggers or [],
        "identity": p.identity, "lifestyle": p.lifestyle or [], "language": p.language or [],
        "behavior": p.behavior, "jobs_to_be_done": p.jobs_to_be_done or [],
        "emotional_triggers": p.emotional_triggers or [], "targeting": p.targeting,
        "created_at": p.created_at.isoformat(),
    }
