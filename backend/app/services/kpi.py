"""KPI aggregation + comparison logic used by the client dashboard."""
from __future__ import annotations

import calendar
import datetime as dt
from typing import Any, Optional

# All KPI cards surfaced on the dashboard, in display order.
KPI_DEFS = [
    ("revenue", "Revenue", "currency", "sum"),
    ("orders", "Orders", "number", "sum"),
    ("roas", "ROAS", "ratio", "avg"),
    ("ad_spend", "Ad Spend", "currency", "sum"),
    ("ctr", "CTR", "percent", "avg"),
    ("cpa", "CPA", "currency", "avg"),
    ("cpm", "CPM", "currency", "avg"),
    ("conversion_rate", "Conversion Rate", "percent", "avg"),
    ("aov", "AOV", "currency", "avg"),
    ("revenue_growth", "Revenue Growth", "percent", "avg"),
    ("sessions", "Website Sessions", "number", "sum"),
    ("returning_customers", "Returning Customers", "number", "sum"),
    ("new_customers", "New Customers", "number", "sum"),
    ("profit_estimate", "Profit Estimate", "currency", "sum"),
    ("lead_count", "Lead Count", "number", "sum"),
    ("whatsapp_leads", "WhatsApp Leads", "number", "sum"),
    ("phone_calls", "Phone Calls", "number", "sum"),
]

# Lower-is-better metrics (a decrease is a positive delta for the client).
INVERSE = {"cpa", "cpm"}


def resolve_range(
    range_key: str,
    custom_from: Optional[dt.date] = None,
    custom_to: Optional[dt.date] = None,
    today: Optional[dt.date] = None,
) -> tuple[dt.date, dt.date, dt.date, dt.date]:
    """Return (start, end, prev_start, prev_end) for a named range."""
    today = today or dt.date.today()

    if range_key == "today":
        start = end = today
    elif range_key == "yesterday":
        start = end = today - dt.timedelta(days=1)
    elif range_key == "7d":
        end, start = today, today - dt.timedelta(days=6)
    elif range_key == "30d":
        end, start = today, today - dt.timedelta(days=29)
    elif range_key in ("90d", "quarter"):
        end, start = today, today - dt.timedelta(days=89)
    elif range_key in ("6m", "180d"):
        end, start = today, today - dt.timedelta(days=179)
    elif range_key in ("1y", "12m", "365d"):
        end, start = today, today - dt.timedelta(days=364)
    elif range_key in ("all", "max"):
        end, start = today, today - dt.timedelta(days=3650)
    elif range_key == "last_month":
        first_this = today.replace(day=1)
        end = first_this - dt.timedelta(days=1)
        start = end.replace(day=1)
    elif range_key == "custom" and custom_from and custom_to:
        start, end = custom_from, custom_to
    else:  # default 30d
        end, start = today, today - dt.timedelta(days=29)

    span = (end - start).days + 1
    prev_end = start - dt.timedelta(days=1)
    prev_start = prev_end - dt.timedelta(days=span - 1)
    return start, end, prev_start, prev_end


def aggregate(rows: list[Any]) -> dict[str, float]:
    """Aggregate metric rows into a single dict.

    Additive metrics (revenue, orders, spend, clicks…) are summed. Ratio metrics
    (ROAS, AOV, CTR, CPA, CPM, conversion rate) are recomputed from the period
    TOTALS — averaging per-day ratios (including zero-days) badly understates them
    (e.g. true AOV = total revenue / total orders, not the mean of daily AOVs).
    """
    def s(key: str) -> float:
        return sum(float(getattr(r, key, 0) or 0) for r in rows)

    # Additive base + display metrics
    additive = ("revenue", "orders", "ad_spend", "impressions", "clicks", "reach",
                "sessions", "returning_customers", "new_customers", "profit_estimate",
                "lead_count", "whatsapp_leads", "phone_calls")
    out: dict[str, float] = {k: round(s(k), 2) for k in additive}

    rev, spend, orders = out["revenue"], out["ad_spend"], out["orders"]
    impr, clicks = out["impressions"], out["clicks"]

    # Ratio metrics derived from the totals above
    out["roas"] = round(rev / spend, 2) if spend else 0.0
    out["aov"] = round(rev / orders, 2) if orders else 0.0
    out["ctr"] = round(clicks / impr * 100, 2) if impr else 0.0
    out["cpa"] = round(spend / orders, 2) if orders else 0.0
    out["cpm"] = round(spend / impr * 1000, 2) if impr else 0.0
    out["conversion_rate"] = round(orders / clicks * 100, 2) if clicks else 0.0

    # revenue_growth has no natural total — keep the period mean of daily values
    n = len(rows) or 1
    out["revenue_growth"] = round(s("revenue_growth") / n, 2)
    return out


def _delta(cur: float, prev: float, key: str) -> float:
    if prev == 0:
        return 0.0
    d = (cur - prev) / abs(prev) * 100
    if key in INVERSE:
        d = -d
    return round(d, 1)


def build_kpi_cards(cur: dict[str, float], prev: dict[str, float]) -> list[dict[str, Any]]:
    cards = []
    for key, label, fmt, _agg in KPI_DEFS:
        cards.append({
            "key": key,
            "label": label,
            "value": cur.get(key, 0),
            "format": fmt,
            "delta": _delta(cur.get(key, 0), prev.get(key, 0), key),
        })
    return cards
