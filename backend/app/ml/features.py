"""Feature extraction for the predictive models."""
from __future__ import annotations

import re
from typing import Any

POWER_WORDS = {
    "free", "new", "proven", "instantly", "guaranteed", "secret", "finally",
    "stop", "warning", "you", "your", "now", "today", "save", "results",
    "without", "never", "easy", "fast", "discover",
}
EMOTION_WORDS = {
    "love", "hate", "fear", "tired", "sick", "frustrated", "obsessed",
    "confidence", "embarrassing", "proud", "guilt", "relief", "dream",
    "struggle", "pain", "happy", "stress",
}


def creative_text_features(text: str, kind: str, framework: str) -> dict[str, float]:
    words = re.findall(r"[A-Za-z']+", text.lower())
    n = max(1, len(words))
    sentences = max(1, len(re.findall(r"[.!?]+", text)) or 1)
    first_line = text.strip().split("\n")[0]

    feats: dict[str, float] = {
        "word_count": float(len(words)),
        "avg_word_len": sum(len(w) for w in words) / n,
        "words_per_sentence": len(words) / sentences,
        "question_marks": float(text.count("?")),
        "exclamations": float(text.count("!")),
        "digits": float(len(re.findall(r"\d", text))),
        "power_word_ratio": sum(w in POWER_WORDS for w in words) / n,
        "emotion_word_ratio": sum(w in EMOTION_WORDS for w in words) / n,
        "second_person": (words.count("you") + words.count("your")) / n,
        "first_line_len": float(len(first_line.split())),
        "has_cta_verb": float(bool(re.search(
            r"\b(shop|get|try|start|claim|grab|join|book|order|discover|learn)\b", text.lower()))),
        "caps_ratio": sum(c.isupper() for c in text) / max(1, len(text)),
        "line_breaks": float(text.count("\n")),
        "emoji_count": float(len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", text))),
    }
    # kind/framework one-hot-ish signals
    feats[f"kind_{kind}"] = 1.0
    feats[f"fw_{framework.lower()}"] = 1.0
    return feats


def campaign_features(campaign: Any) -> dict[str, float]:
    """Features from a live Campaign row (existing CRUX model)."""
    spend = campaign.spend or 0.0
    impressions = max(1, campaign.impressions or 0)
    clicks = campaign.clicks or 0
    return {
        "spend": spend,
        "impressions": float(impressions),
        "ctr": campaign.ctr or (clicks / impressions * 100),
        "cpm": campaign.cpm or (spend / impressions * 1000),
        "frequency": campaign.frequency or 0.0,
        "cpa": campaign.cpa or 0.0,
        "roas": campaign.purchase_roas or 0.0,
        "conversions": float(campaign.conversions or 0),
        "reach_ratio": (campaign.reach or 0) / impressions,
    }
