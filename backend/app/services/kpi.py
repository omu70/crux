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
    elif range_key == "last_month":
        first_this = today.replace(day=1)
        end = first_this - dt.timedelta(days=1)
        start = end.replace(day=1)
    elif range_key == "quarter":
        end, start = today, today - dt.timedelta(days=89)
    elif range_key == "custom" and custom_from and custom_to:
        start, end = custom_from, custom_to
    else:  # default 30d
        end, start = today, today - dt.timedelta(days=29)

    span = (end - start).days + 1
    prev_end = start - dt.timedelta(days=1)
    prev_start = prev_end - dt.timedelta(days=span - 1)
    return start, end, prev_start, prev_end


def aggregate(rows: list[Any]) -> dict[str, float]:
    """Aggregate metric rows into a single dict per KPI_DEFS rules."""
    out: dict[str, float] = {}
    n = len(rows) or 1
    for key, _label, _fmt, agg in KPI_DEFS:
        vals = [float(getattr(r, key, 0) or 0) for r in rows]
        total = sum(vals)
        out[key] = round(total / n, 2) if agg == "avg" else round(total, 2)
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
