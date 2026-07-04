"""AI insight generation.

Uses Google Gemini when GEMINI_API_KEY is configured; otherwise falls back to a
deterministic, rule-based analysis so the product is always useful even without
an API key. The public functions return plain dicts ready to persist as
AiInsight rows or render directly.
"""
from __future__ import annotations

from typing import Any

from app.core.config import settings


def _gemini_available() -> bool:
    if not settings.GEMINI_API_KEY:
        return False
    try:
        import google.generativeai  # noqa: F401
        return True
    except Exception:
        return False


def _rule_based_insights(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive insights from the last vs previous period of daily metrics."""
    if not metrics:
        return [{
            "title": "Connect your data sources",
            "body": "No performance data yet. Connect Meta Ads, Shopify and GA4 to unlock daily AI insights.",
            "category": "recommendation",
            "impact": "MEDIUM",
        }]

    recent = metrics[-7:]
    prev = metrics[-14:-7] if len(metrics) >= 14 else metrics[:len(recent)]

    def avg(rows, key):
        vals = [r.get(key, 0) or 0 for r in rows]
        return sum(vals) / len(vals) if vals else 0

    def pct(cur, old):
        if old == 0:
            return 0.0
        return round((cur - old) / old * 100, 1)

    roas_now, roas_prev = avg(recent, "roas"), avg(prev, "roas")
    rev_now, rev_prev = avg(recent, "revenue"), avg(prev, "revenue")
    ctr_now, ctr_prev = avg(recent, "ctr"), avg(prev, "ctr")
    cpa_now, cpa_prev = avg(recent, "cpa"), avg(prev, "cpa")
    cr_now, cr_prev = avg(recent, "conversion_rate"), avg(prev, "conversion_rate")

    out: list[dict[str, Any]] = []

    d = pct(roas_now, roas_prev)
    if d >= 5:
        out.append({"title": f"ROAS increased by {d}%", "body": f"Blended ROAS climbed to {roas_now:.2f}x over the last 7 days. Consider scaling spend on top campaigns by ~20% while efficiency holds.", "category": "performance", "impact": "HIGH"})
    elif d <= -5:
        out.append({"title": f"ROAS dropped by {abs(d)}%", "body": f"Blended ROAS fell to {roas_now:.2f}x. Review frequency and creative fatigue on your highest-spend ad sets.", "category": "warning", "impact": "HIGH"})

    d = pct(ctr_now, ctr_prev)
    if d <= -8:
        out.append({"title": "CTR has dropped", "body": f"Average CTR is down {abs(d)}% week-over-week — a classic creative-fatigue signal. Refresh top-of-funnel creatives.", "category": "warning", "impact": "MEDIUM"})

    d = pct(cpa_now, cpa_prev)
    if d >= 10:
        out.append({"title": f"CPA is rising ({d}%)", "body": f"Cost per acquisition increased to ${cpa_now:.2f}. Tighten audience targeting and pause under-performing ads.", "category": "warning", "impact": "HIGH"})

    d = pct(cr_now, cr_prev)
    if d <= -5:
        out.append({"title": "Landing page conversion rate decreased", "body": f"On-site conversion rate slipped {abs(d)}%. Audit page speed and checkout friction.", "category": "warning", "impact": "MEDIUM"})

    d = pct(rev_now, rev_prev)
    if d >= 5:
        out.append({"title": f"Revenue trending up {d}%", "body": "Momentum is strong. Retarget Add-To-Cart audiences and test an Advantage+ shopping campaign to compound growth.", "category": "opportunity", "impact": "MEDIUM"})

    if not out:
        out.append({"title": "Performance is stable", "body": "Metrics are holding steady week-over-week. A budget test of +15% on your best ROAS campaign could unlock incremental volume.", "category": "recommendation", "impact": "LOW"})
    return out


def generate_insights(client_name: str, metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a list of insight dicts. Falls back gracefully without a key."""
    if not _gemini_available():
        return _rule_based_insights(metrics)
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "You are a senior performance-marketing analyst for the agency DiziGroww. "
            f"Analyse this client's ({client_name}) recent daily marketing metrics and produce 3-5 "
            "concise, specific, action-oriented insights. Return a JSON array of objects with keys "
            "title, body, category (performance|warning|opportunity|recommendation), impact (LOW|MEDIUM|HIGH). "
            f"Metrics (most recent last): {metrics[-14:]}"
        )
        resp = model.generate_content(prompt)
        import json
        text = resp.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return _rule_based_insights(metrics)


def generate_plan_of_action(metrics: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Turn insights into a today / this-week / this-month action plan."""
    insights = _rule_based_insights(metrics)
    plan = {"today": [], "week": [], "month": []}
    buckets = ["today", "week", "month"]
    for i, ins in enumerate(insights):
        bucket = buckets[min(i, 2)]
        plan[bucket].append({
            "title": ins["title"].replace("increased", "capitalise on").replace("dropped", "fix"),
            "priority": ins["impact"],
            "expected_result": ins["body"][:120],
        })
    return plan
