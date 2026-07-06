"""Visual AI — score ad creatives with vision models (GPT-4o / Gemini vision),
falling back to a deterministic heuristic scorer.

analyze_image_scores(image_url_or_b64, kind, brand_context) returns:
    {creative_score, attention_score, scroll_stop_score, brand_score,
     emotion_score, ctr_prediction, recommendations: [str], observations: [str]}
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.ai import mock
from app.ai.providers import GEMINI, OPENAI
from app.core.config import settings

log = logging.getLogger("aether.vision")

_SHAPE = {
    "creative_score": "score",
    "attention_score": "score",
    "scroll_stop_score": "score",
    "brand_score": "score",
    "emotion_score": "score",
    "ctr_prediction": "pct",
    "recommendations": ["recommendation"],
    "observations": ["What the model noticed about composition, color, faces, text overlay"],
}

_SYSTEM = (
    "You are a world-class creative strategist and paid-social analyst. You audit ad "
    "creatives for Meta placements. Score 0-100 on each dimension: creative (overall "
    "craft), attention (visual hierarchy pulls the eye), scroll_stop (pattern-interrupt "
    "strength in a feed), brand (distinctiveness + consistency with the brand context "
    "given), emotion (evoked feeling intensity and relevance). Predict feed CTR as a "
    "percentage (typical range 0.5-3.5). Give concrete, testable recommendations."
)


def _vision_prompt(kind: str, brand_context: str) -> str:
    return (
        f"Audit this {kind} ad creative. Brand context: {brand_context or 'unknown brand'}. "
        "Assess: focal hierarchy, thumb-stop strength in the first 0.5s, color contrast vs a "
        "typical feed, presence/absence of faces, text-overlay hook quality, offer clarity, "
        "brand distinctiveness, emotional charge."
    )


def _openai_vision(image_url: str, kind: str, brand_context: str) -> dict[str, Any]:
    import json as _json
    body = {
        "model": settings.LLM_DEFAULT_MODEL,
        "response_format": {"type": "json_object"},
        "max_tokens": 1200,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": [
                {"type": "text", "text": _vision_prompt(kind, brand_context) +
                 "\nRespond ONLY with JSON matching: " + _json.dumps(_SHAPE)},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]},
        ],
    }
    r = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
        json=body, timeout=settings.LLM_TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    import json
    return json.loads(r.json()["choices"][0]["message"]["content"])


def _gemini_vision(image_url: str, kind: str, brand_context: str) -> dict[str, Any]:
    import base64
    import json as _json
    img = httpx.get(image_url, timeout=30, follow_redirects=True)
    img.raise_for_status()
    mime = img.headers.get("content-type", "image/jpeg").split(";")[0]
    b64 = base64.b64encode(img.content).decode()
    body = {
        "contents": [{"role": "user", "parts": [
            {"text": _SYSTEM + "\n" + _vision_prompt(kind, brand_context) +
             "\nRespond ONLY with JSON matching: " + _json.dumps(_SHAPE)},
            {"inlineData": {"mimeType": mime, "data": b64}},
        ]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 1200},
    }
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent",
        params={"key": settings.GEMINI_API_KEY}, json=body,
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    import json
    parts = r.json()["candidates"][0]["content"]["parts"]
    return json.loads("".join(p.get("text", "") for p in parts))


def analyze_image_scores(image_url: str, kind: str = "image",
                         brand_context: str = "") -> dict[str, Any]:
    for fn, name in ((_openai_vision, "openai"), (_gemini_vision, "gemini")):
        provider = OPENAI if name == "openai" else GEMINI
        if not provider.available():
            continue
        try:
            data = fn(image_url, kind, brand_context)
            data["provider"] = name
            return _clamp(data)
        except Exception as exc:
            log.warning("%s vision failed: %s", name, exc)
    data = mock.mock_json(f"visual analysis {image_url} {kind} {brand_context}", _SHAPE)
    data["provider"] = "mock"
    return _clamp(data)


def _clamp(d: dict[str, Any]) -> dict[str, Any]:
    for k in ("creative_score", "attention_score", "scroll_stop_score", "brand_score", "emotion_score"):
        try:
            d[k] = max(0, min(100, int(d.get(k, 0))))
        except (TypeError, ValueError):
            d[k] = 50
    try:
        d["ctr_prediction"] = max(0.05, min(15.0, float(d.get("ctr_prediction", 1.0))))
    except (TypeError, ValueError):
        d["ctr_prediction"] = 1.0
    d.setdefault("recommendations", [])
    d.setdefault("observations", [])
    return d
