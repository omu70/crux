"""Module 5 — Visual AI: score images/videos/products/packaging for ad use."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.ai.vision import analyze_image_scores
from app.models.aether import VisualAnalysis
from app.models.models import Client
from app.modules.business_intel import business_context_snippet

log = logging.getLogger("aether.visual")


def analyze_visual(db: Session, client: Client, asset_url: str,
                   kind: str = "image") -> VisualAnalysis:
    brand_ctx = business_context_snippet(db, client.id, max_chars=1200)
    scores = analyze_image_scores(asset_url, kind=kind, brand_context=brand_ctx)
    row = VisualAnalysis(
        client_id=client.id, asset_url=asset_url[:600], kind=kind,
        creative_score=scores["creative_score"],
        attention_score=scores["attention_score"],
        scroll_stop_score=scores["scroll_stop_score"],
        brand_score=scores["brand_score"],
        emotion_score=scores["emotion_score"],
        ctr_prediction=scores["ctr_prediction"],
        recommendations=scores.get("recommendations"),
        raw=scores,
    )
    db.add(row)
    db.commit()
    return row


def serialize_visual(v: VisualAnalysis) -> dict:
    return {
        "id": v.id, "asset_url": v.asset_url, "kind": v.kind,
        "creative_score": v.creative_score, "attention_score": v.attention_score,
        "scroll_stop_score": v.scroll_stop_score, "brand_score": v.brand_score,
        "emotion_score": v.emotion_score, "ctr_prediction": round(v.ctr_prediction, 2),
        "recommendations": v.recommendations or [],
        "observations": (v.raw or {}).get("observations", []),
        "provider": (v.raw or {}).get("provider"),
        "created_at": v.created_at.isoformat(),
    }
