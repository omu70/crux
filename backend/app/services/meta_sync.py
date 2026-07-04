"""Pull Meta Ads insights and map them into CRUX's data model.

Reads the client's META_ADS integration config (ad_account_id, optional
access_token — falls back to the META_ACCESS_TOKEN env var), fetches campaign +
daily account insights from the Marketing API, and upserts Campaign and
MetricSnapshot rows so the dashboard shows real numbers.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy.orm import Session

from app.models import Campaign, Client, Integration, MetricSnapshot
from app.services.integrations import MetaAdsClient

# Meta reports purchases under several action_type aliases depending on setup.
PURCHASE_TYPES = {"purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"}


def _f(x: Any) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _i(x: Any) -> int:
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


def action_value(items: list[dict[str, Any]] | None, types: set[str]) -> float:
    """Sum the `value` of matching action_type entries in a Meta actions list."""
    total = 0.0
    for it in items or []:
        if it.get("action_type") in types:
            total += _f(it.get("value"))
    return total


def map_campaign(row: Campaign, c: dict[str, Any]) -> None:
    spend = _f(c.get("spend"))
    conv = int(action_value(c.get("actions"), PURCHASE_TYPES))
    revenue = action_value(c.get("action_values"), PURCHASE_TYPES)
    roas = action_value(c.get("purchase_roas"), PURCHASE_TYPES) or (revenue / spend if spend else 0)
    row.name = c.get("campaign_name") or "Campaign"
    row.spend = spend
    row.impressions = _i(c.get("impressions"))
    row.clicks = _i(c.get("clicks"))
    row.ctr = _f(c.get("ctr"))
    row.cpm = _f(c.get("cpm"))
    row.reach = _i(c.get("reach"))
    row.frequency = _f(c.get("frequency"))
    row.conversions = conv
    row.revenue = revenue
    row.purchase_roas = round(roas, 2)
    row.cpa = round(spend / conv, 2) if conv else 0


def map_daily(row: MetricSnapshot, d: dict[str, Any]) -> None:
    spend = _f(d.get("spend"))
    conv = int(action_value(d.get("actions"), PURCHASE_TYPES))
    revenue = action_value(d.get("action_values"), PURCHASE_TYPES)
    clicks = _i(d.get("clicks"))
    row.ad_spend = spend
    row.revenue = revenue
    row.orders = conv
    row.impressions = _i(d.get("impressions"))
    row.clicks = clicks
    row.ctr = _f(d.get("ctr"))
    row.cpm = _f(d.get("cpm"))
    row.reach = _i(d.get("reach"))
    row.roas = round(action_value(d.get("purchase_roas"), PURCHASE_TYPES) or (revenue / spend if spend else 0), 2)
    row.cpa = round(spend / conv, 2) if conv else 0
    row.aov = round(revenue / conv, 2) if conv else 0
    row.conversion_rate = round(conv / clicks * 100, 2) if clicks else 0


def sync_meta(db: Session, client: Client, date_preset: str = "last_30d") -> dict[str, Any]:
    """Sync Meta data for a client. Raises ValueError if not configured."""
    integ = (
        db.query(Integration)
        .filter(Integration.client_id == client.id, Integration.type == "META_ADS")
        .first()
    )
    if integ is None:
        raise ValueError("Meta Ads is not connected for this client.")

    config = integ.config or {}
    client_api = MetaAdsClient(config.get("ad_account_id"), config.get("access_token"))
    if not client_api.is_configured():
        raise ValueError("Missing Meta Ad Account ID or access token (set META_ACCESS_TOKEN or per-client token).")

    # Campaigns (upsert by external campaign id)
    n_camp = 0
    for c in client_api.fetch_campaign_insights(date_preset):
        ext = c.get("campaign_id")
        row = (
            db.query(Campaign)
            .filter(Campaign.client_id == client.id, Campaign.external_id == ext)
            .first()
        )
        if row is None:
            row = Campaign(client_id=client.id, external_id=ext, status="ACTIVE")
            db.add(row)
        map_campaign(row, c)
        n_camp += 1

    # Flag winning / losing by ROAS (flush first so new campaigns are visible)
    db.flush()
    all_camps = db.query(Campaign).filter(Campaign.client_id == client.id).all()
    if all_camps:
        best = max(all_camps, key=lambda x: x.purchase_roas)
        worst = min(all_camps, key=lambda x: x.purchase_roas)
        for cp in all_camps:
            cp.is_winning = cp.id == best.id and best.purchase_roas > 0
            cp.is_losing = cp.id == worst.id and worst.purchase_roas < 1 and worst.spend > 0

    # Daily account metrics (upsert by date)
    n_day = 0
    for d in client_api.fetch_daily_insights(date_preset):
        date_str = d.get("date_start")
        if not date_str:
            continue
        date = dt.date.fromisoformat(date_str)
        row = (
            db.query(MetricSnapshot)
            .filter(MetricSnapshot.client_id == client.id, MetricSnapshot.date == date)
            .first()
        )
        if row is None:
            row = MetricSnapshot(client_id=client.id, date=date)
            db.add(row)
        map_daily(row, d)
        n_day += 1

    integ.status = "CONNECTED"
    integ.last_synced_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return {"campaigns_synced": n_camp, "days_synced": n_day,
            "ad_account_id": config.get("ad_account_id")}
