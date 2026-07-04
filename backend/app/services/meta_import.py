"""Import a Meta Ads Manager export (CSV or Excel) into CRUX.

Meta's exports don't have fixed column names — they depend on which columns the
user added to their Ads Manager view. So we auto-detect columns by fuzzy-matching
common Meta header names, then upsert daily MetricSnapshot rows (grouped by day)
and Campaign rows (grouped by campaign name).
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import Campaign, Client, MetricSnapshot


# ── File parsing ─────────────────────────────────────────────────────────────
def parse_table(filename: str, content: bytes) -> list[dict[str, Any]]:
    """Return a list of row dicts keyed by original header names."""
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xls")):
        try:
            import openpyxl
        except Exception as exc:  # pragma: no cover
            raise ValueError("Excel support needs openpyxl; please export as CSV instead.") from exc
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h).strip() if h is not None else "" for h in rows[0]]
        return [dict(zip(headers, r)) for r in rows[1:]]

    # CSV (utf-8-sig strips Meta's BOM)
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(r) for r in reader]


# ── Column detection ─────────────────────────────────────────────────────────
def _norm(h: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (h or "").lower())).strip()


def detect_column(header: str) -> str | None:
    """Map a Meta export header to a CRUX metric key (or None)."""
    h = _norm(header)
    if not h:
        return None
    if h in ("day", "date") or h.startswith("reporting starts"):
        return "date"
    if "campaign name" in h or h == "campaign":
        return "campaign"
    # revenue must be checked before 'purchases' (it contains the word)
    if "conversion value" in h or ("purchase" in h and "value" in h):
        return "revenue"
    if "roas" in h or "return on ad spend" in h:
        return "roas"
    if "amount spent" in h or h in ("spend", "cost", "amount"):
        return "spend"
    if h.startswith("cpm"):
        return "cpm"
    if h.startswith("ctr"):
        return "ctr"
    if h == "impressions":
        return "impressions"
    if "link click" in h or h in ("clicks", "clicks all"):
        return "clicks"
    if h == "reach":
        return "reach"
    if h == "frequency":
        return "frequency"
    if h in ("purchases", "website purchases", "results", "meta purchases") or "purchase" in h:
        return "conversions"
    return None


# ── Value / date cleaning ────────────────────────────────────────────────────
def _num(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return float(s) if s not in ("", "-", ".") else 0.0
    except ValueError:
        return 0.0


_DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y", "%d %b %Y", "%B %d, %Y"]


def _parse_date(v: Any) -> dt.date | None:
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v).strip()
    try:
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _blank_agg() -> dict[str, float]:
    return {k: 0.0 for k in ("spend", "impressions", "clicks", "reach", "conversions", "revenue")}


# ── Import ───────────────────────────────────────────────────────────────────
def import_meta_export(db: Session, client: Client, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("The file has no rows.")

    colmap = {h: detect_column(h) for h in rows[0].keys()}
    keys = set(colmap.values())
    if "date" not in keys and "campaign" not in keys:
        raise ValueError("Couldn't find a 'Day'/date or 'Campaign name' column. "
                         "Add a Day breakdown or Campaign name column to your Meta export.")

    def get(row: dict[str, Any], key: str) -> Any:
        for header, mapped in colmap.items():
            if mapped == key:
                return row.get(header)
        return None

    daily: dict[dt.date, dict[str, float]] = {}
    camps: dict[str, dict[str, float]] = {}

    for row in rows:
        spend = _num(get(row, "spend"))
        impressions = _num(get(row, "impressions"))
        clicks = _num(get(row, "clicks"))
        reach = _num(get(row, "reach"))
        conv = _num(get(row, "conversions"))
        revenue = _num(get(row, "revenue"))

        date = _parse_date(get(row, "date"))
        if date:
            agg = daily.setdefault(date, _blank_agg())
            agg["spend"] += spend
            agg["impressions"] += impressions
            agg["clicks"] += clicks
            agg["reach"] += reach
            agg["conversions"] += conv
            agg["revenue"] += revenue

        name = get(row, "campaign")
        if name and str(name).strip():
            agg = camps.setdefault(str(name).strip(), _blank_agg())
            agg["spend"] += spend
            agg["impressions"] += impressions
            agg["clicks"] += clicks
            agg["reach"] += reach
            agg["conversions"] += conv
            agg["revenue"] += revenue

    # Upsert daily metrics
    for date, a in daily.items():
        row = (db.query(MetricSnapshot)
               .filter(MetricSnapshot.client_id == client.id, MetricSnapshot.date == date).first())
        if row is None:
            row = MetricSnapshot(client_id=client.id, date=date)
            db.add(row)
        conv = a["conversions"]
        row.ad_spend = round(a["spend"], 2)
        row.revenue = round(a["revenue"], 2)
        row.orders = int(conv)
        row.impressions = int(a["impressions"])
        row.clicks = int(a["clicks"])
        row.reach = int(a["reach"])
        row.roas = round(a["revenue"] / a["spend"], 2) if a["spend"] else 0
        row.ctr = round(a["clicks"] / a["impressions"] * 100, 2) if a["impressions"] else 0
        row.cpm = round(a["spend"] / a["impressions"] * 1000, 2) if a["impressions"] else 0
        row.cpa = round(a["spend"] / conv, 2) if conv else 0
        row.aov = round(a["revenue"] / conv, 2) if conv else 0
        row.conversion_rate = round(conv / a["clicks"] * 100, 2) if a["clicks"] else 0

    # Upsert campaigns
    for name, a in camps.items():
        row = (db.query(Campaign)
               .filter(Campaign.client_id == client.id, Campaign.name == name).first())
        if row is None:
            row = Campaign(client_id=client.id, name=name, status="ACTIVE")
            db.add(row)
        conv = a["conversions"]
        row.spend = round(a["spend"], 2)
        row.revenue = round(a["revenue"], 2)
        row.conversions = int(conv)
        row.impressions = int(a["impressions"])
        row.clicks = int(a["clicks"])
        row.reach = int(a["reach"])
        row.purchase_roas = round(a["revenue"] / a["spend"], 2) if a["spend"] else 0
        row.ctr = round(a["clicks"] / a["impressions"] * 100, 2) if a["impressions"] else 0
        row.cpm = round(a["spend"] / a["impressions"] * 1000, 2) if a["impressions"] else 0
        row.cpa = round(a["spend"] / conv, 2) if conv else 0

    # Winning / losing flags (flush first so newly-added campaigns are visible)
    db.flush()
    all_camps = db.query(Campaign).filter(Campaign.client_id == client.id).all()
    if all_camps:
        best = max(all_camps, key=lambda x: x.purchase_roas)
        worst = min(all_camps, key=lambda x: x.purchase_roas)
        for cp in all_camps:
            cp.is_winning = cp.id == best.id and best.purchase_roas > 0
            cp.is_losing = cp.id == worst.id and worst.spend > 0 and worst.purchase_roas < 1

    db.commit()
    detected = sorted({v for v in colmap.values() if v})
    return {"days_imported": len(daily), "campaigns_imported": len(camps), "columns_detected": detected}
