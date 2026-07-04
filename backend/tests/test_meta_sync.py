"""Unit tests for Meta insight parsing (no network / DB needed)."""
from types import SimpleNamespace

from app.services.meta_sync import PURCHASE_TYPES, action_value, map_campaign, map_daily


def test_action_value_picks_purchase():
    items = [{"action_type": "link_click", "value": "250"},
             {"action_type": "purchase", "value": "20"}]
    assert action_value(items, PURCHASE_TYPES) == 20.0
    assert action_value(None, PURCHASE_TYPES) == 0.0
    assert action_value([], PURCHASE_TYPES) == 0.0


def test_map_campaign():
    c = {
        "campaign_id": "123", "campaign_name": "Summer Sale",
        "spend": "100.50", "impressions": "10000", "clicks": "250",
        "ctr": "2.5", "cpm": "10.05", "reach": "8000", "frequency": "1.25",
        "actions": [{"action_type": "purchase", "value": "20"}],
        "action_values": [{"action_type": "purchase", "value": "1500.00"}],
        "purchase_roas": [{"action_type": "purchase", "value": "14.9"}],
    }
    row = SimpleNamespace()
    map_campaign(row, c)
    assert row.name == "Summer Sale"
    assert row.spend == 100.5
    assert row.conversions == 20
    assert row.revenue == 1500.0
    assert row.purchase_roas == 14.9
    assert 5.0 <= row.cpa <= 5.05          # 100.5 / 20


def test_map_daily():
    d = {
        "date_start": "2026-07-01", "spend": "50", "clicks": "100",
        "impressions": "5000", "cpm": "10", "reach": "4000",
        "actions": [{"action_type": "purchase", "value": "5"}],
        "action_values": [{"action_type": "purchase", "value": "400"}],
        "purchase_roas": [{"action_type": "purchase", "value": "8"}],
    }
    row = SimpleNamespace()
    map_daily(row, d)
    assert row.ad_spend == 50.0
    assert row.orders == 5
    assert row.revenue == 400.0
    assert row.roas == 8.0
    assert row.aov == 80.0                  # 400 / 5
    assert row.conversion_rate == 5.0       # 5 / 100 * 100
    assert row.cpa == 10.0                  # 50 / 5
