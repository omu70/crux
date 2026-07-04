"""Pull WooCommerce orders into CRUX.

Reads the client's WOOCOMMERCE integration config (url, key, secret), fetches
recent orders from the WooCommerce REST API, upserts them into the Order table
(the e-commerce tab), and rolls paid orders up into daily revenue/orders on the
MetricSnapshot rows so the KPIs + charts reflect real store sales.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session

from app.models import Client, Integration, MetricSnapshot, Order
from app.services.integrations import WooCommerceClient

# WooCommerce status → CRUX OrderStatus
_STATUS = {
    "completed": "PAID", "processing": "PAID",
    "refunded": "REFUNDED",
    "cancelled": "CANCELLED", "failed": "CANCELLED",
    "pending": "PENDING", "on-hold": "PENDING",
}


def _num(x: Any) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _parse_dt(v: Any) -> dt.datetime | None:
    if not v:
        return None
    s = str(v).replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        try:
            return dt.datetime.fromisoformat(s[:19])
        except ValueError:
            return None


def map_order(row: Order, o: dict[str, Any]) -> dt.datetime | None:
    billing = o.get("billing") or {}
    name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or "Guest"
    created = _parse_dt(o.get("date_created") or o.get("date_created_gmt"))
    row.order_number = f"#{o.get('number') or o.get('id')}"
    row.customer_name = name
    row.total = round(_num(o.get("total")), 2)
    row.status = _STATUS.get(str(o.get("status", "")).lower(), "PENDING")
    row.items_count = len(o.get("line_items") or []) or 1
    row.source = "woocommerce"
    if created:
        row.created_at = created
    return created


def sync_woo(db: Session, client: Client) -> dict[str, Any]:
    integ = (db.query(Integration)
             .filter(Integration.client_id == client.id, Integration.type == "WOOCOMMERCE").first())
    if integ is None:
        raise ValueError("WooCommerce is not connected for this client.")
    cfg = integ.config or {}
    api = WooCommerceClient(cfg.get("url"), cfg.get("key"), cfg.get("secret"))
    if not api.is_configured():
        raise ValueError("Missing WooCommerce store URL, key or secret.")

    orders = api.fetch_orders()
    daily: dict[dt.date, dict[str, float]] = {}
    n = 0
    for o in orders:
        ext = str(o.get("id"))
        row = (db.query(Order)
               .filter(Order.client_id == client.id, Order.external_id == ext).first())
        if row is None:
            row = Order(client_id=client.id, external_id=ext)
            db.add(row)
        created = map_order(row, o)
        n += 1
        if row.status == "PAID" and created:
            agg = daily.setdefault(created.date(), {"revenue": 0.0, "orders": 0.0})
            agg["revenue"] += row.total
            agg["orders"] += 1

    # Roll paid orders into daily metrics (revenue / orders / AOV; ROAS if ad spend known)
    for date, a in daily.items():
        m = (db.query(MetricSnapshot)
             .filter(MetricSnapshot.client_id == client.id, MetricSnapshot.date == date).first())
        if m is None:
            m = MetricSnapshot(client_id=client.id, date=date)
            db.add(m)
        m.revenue = round(a["revenue"], 2)
        m.orders = int(a["orders"])
        m.aov = round(a["revenue"] / a["orders"], 2) if a["orders"] else 0
        if m.ad_spend:
            m.roas = round(a["revenue"] / m.ad_spend, 2)

    integ.status = "CONNECTED"
    integ.last_synced_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return {"orders_synced": n, "days_updated": len(daily)}
