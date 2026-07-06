"""Deterministic mock LLM.

Every Aether feature must work with zero API keys (local dev, demos, tests,
CI). The mock produces stable, plausible, schema-correct JSON keyed by a hash
of the prompt, so the same input always yields the same output.

The mock inspects the `shape` hint passed by callers (each module passes the
JSON skeleton it expects) and fills it with content assembled from the prompt
context. It is intentionally simple — the point is structural correctness and
believable demo data, not intelligence.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from typing import Any


def _seed_from(text: str) -> random.Random:
    digest = hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()
    return random.Random(int(digest[:12], 16))


def _extract_subject(prompt: str) -> str:
    """Best-effort subject (brand/product) mention from the prompt context."""
    m = re.search(r"(?:company|brand|business|client)[\s:]+[\"']?([A-Z][\w &.-]{2,40})", prompt)
    if m:
        return m.group(1).strip()
    return "the brand"


_HOOK_PATTERNS = [
    "Stop scrolling if you {pain}",
    "I tried everything for {pain} — this finally worked",
    "Nobody talks about this {category} mistake",
    "POV: you finally fixed {pain}",
    "The 5-second fix for {pain}",
    "Why your {category} routine is failing you",
    "This is your sign to stop settling for {pain}",
    "3 reasons {audience} are switching to {subject}",
    "I was today years old when I learned this about {category}",
    "Warning: this will change how you think about {category}",
]

_HEADLINES = [
    "{subject}: {benefit}, Guaranteed",
    "The Smarter Way To {benefit}",
    "Finally — {benefit} Without {pain}",
    "{benefit} In 30 Days Or Your Money Back",
    "Join 10,000+ {audience} Who {benefit}",
    "Rated 4.8/5 By {audience} Like You",
    "{benefit}. No {pain}. No Compromises.",
    "From {pain} To {benefit} — Here's How",
]

_RECOMMENDATIONS = [
    "Increase contrast between subject and background to lift scroll-stop rate",
    "Move the product 20% closer to the first visual focal point",
    "Add a human face — faces lift attention scores 15-30%",
    "Overlay the core benefit as a 5-7 word text hook in the first frame",
    "Use brand colors more prominently to improve attribution",
    "Tighten the crop; negative space is diluting the focal point",
    "Add social proof element (rating stars / customer count)",
    "Test a version with higher color saturation for feed contrast",
]


def mock_json(prompt: str, shape: Any) -> Any:
    """Fill `shape` deterministically. Strings are template-expanded; lists are
    grown to 3-6 items based on their first element; dicts recurse."""
    rng = _seed_from(prompt)
    subject = _extract_subject(prompt)
    ctx = {
        "subject": subject,
        "pain": rng.choice(["wasting money on ads that don't convert", "inconsistent results",
                            "guesswork", "rising acquisition costs", "creative fatigue"]),
        "benefit": rng.choice(["Better ROAS", "Predictable Growth", "Lower CPA",
                               "Winning Creatives On Demand", "Compounding Results"]),
        "audience": rng.choice(["founders", "marketers", "busy professionals", "shop owners"]),
        "category": rng.choice(["marketing", "growth", "advertising", "ecommerce"]),
    }

    def fill(node: Any, depth: int = 0) -> Any:
        if isinstance(node, dict):
            return {k: fill(v, depth + 1) for k, v in node.items()}
        if isinstance(node, list):
            if not node:
                return []
            proto = node[0]
            n = len(node) if len(node) > 1 else rng.randint(3, 6)
            return [fill(proto, depth + 1) for _ in range(n)]
        if isinstance(node, str):
            token = node.strip().lower()
            # enum hints: "unaware|problem_aware|..." or "APPROVED or REJECTED"
            stripped = node.strip()
            if "|" in stripped and re.fullmatch(r"[\w .+&/-]+(\|[\w .+&/-]+)+", stripped):
                return rng.choice([o.strip() for o in stripped.split("|") if o.strip()])
            m_or = re.fullmatch(r"([A-Z_]+) or ([A-Z_]+)", stripped)
            if m_or:
                return rng.choice([m_or.group(1), m_or.group(2)])
            if token in ("hook",):
                return rng.choice(_HOOK_PATTERNS).format(**ctx)
            if token in ("headline",):
                return rng.choice(_HEADLINES).format(**ctx)
            if token in ("recommendation",):
                return rng.choice(_RECOMMENDATIONS)
            if token in ("score", "int_0_100"):
                return rng.randint(55, 92)
            if token in ("float_0_1", "confidence"):
                return round(rng.uniform(0.55, 0.92), 2)
            if token in ("pct",):
                return round(rng.uniform(0.8, 3.4), 2)
            # generic string: expand {tokens} if present, else synthesize
            try:
                expanded = node.format(**ctx)
            except (KeyError, IndexError):
                expanded = node
            if expanded != node:
                return expanded
            return f"{node} for {subject}".strip()
        if isinstance(node, bool):
            return rng.random() > 0.4
        if isinstance(node, int):
            return rng.randint(max(0, node // 2), max(1, node * 2)) if node else rng.randint(50, 90)
        if isinstance(node, float):
            return round(rng.uniform(node * 0.5, node * 1.5), 3) if node else round(rng.uniform(0.5, 4.0), 2)
        return node

    return fill(shape)


def mock_text(prompt: str) -> str:
    """Deterministic multi-sentence analysis paragraph for free-text asks."""
    rng = _seed_from(prompt)
    subject = _extract_subject(prompt)
    lines = [
        f"{subject} operates in a market where trust and differentiation drive conversion more than price.",
        "The highest-leverage opportunity is sharpening the core offer around a single measurable outcome and rebuilding top-of-funnel creative around customer language rather than product features.",
        rng.choice([
            "Testing should prioritize hook variation over audience variation given current signal volume.",
            "Budget consolidation into fewer, broader ad sets will exit learning phase faster and stabilize CPA.",
            "The funnel's weakest link is the gap between ad promise and landing-page proof; closing it should precede any scale attempt.",
        ]),
    ]
    return " ".join(lines)


def mock_embedding(text: str, dim: int) -> list[float]:
    """Deterministic pseudo-embedding: seeded unit vector. Preserves the key
    property tests rely on — identical text → identical vector — and gives
    loosely similar vectors for texts sharing many character n-grams."""
    rng = _seed_from(text[:2000])
    vec = [rng.uniform(-1, 1) for _ in range(dim)]
    # nudge dimensions by n-gram hashes so related texts correlate
    for gram in {text[i:i + 4].lower() for i in range(0, min(len(text), 800), 4)}:
        h = int(hashlib.md5(gram.encode("utf-8", "ignore")).hexdigest()[:8], 16)
        vec[h % dim] += 0.5
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [round(v / norm, 6) for v in vec]


def looks_like_json_request(prompt: str) -> bool:
    return "json" in prompt.lower()


def mock_complete(prompt: str, shape: Any | None) -> str:
    if shape is not None:
        return json.dumps(mock_json(prompt, shape))
    return mock_text(prompt)
