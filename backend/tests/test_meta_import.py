"""Unit tests for Meta export column detection + value parsing."""
import datetime as dt

from app.services.meta_import import _num, _parse_date, detect_column


def test_detect_columns():
    assert detect_column("Day") == "date"
    assert detect_column("Reporting starts") == "date"
    assert detect_column("Campaign name") == "campaign"
    assert detect_column("Amount spent (USD)") == "spend"
    assert detect_column("Impressions") == "impressions"
    assert detect_column("Link clicks") == "clicks"
    assert detect_column("CTR (link click-through rate)") == "ctr"
    assert detect_column("CPM (cost per 1,000 impressions)") == "cpm"
    assert detect_column("Reach") == "reach"
    # revenue must win over conversions for the value column
    assert detect_column("Purchases conversion value") == "revenue"
    assert detect_column("Purchases") == "conversions"
    assert detect_column("Purchase ROAS (return on ad spend)") == "roas"
    assert detect_column("Some random column") is None


def test_num_cleaning():
    assert _num("1,500.50") == 1500.5
    assert _num("$1,200") == 1200.0
    assert _num("2.5%") == 2.5
    assert _num("--") == 0.0
    assert _num(None) == 0.0
    assert _num(42) == 42.0


def test_date_parsing():
    assert _parse_date("2026-07-01") == dt.date(2026, 7, 1)
    assert _parse_date("07/01/2026") == dt.date(2026, 7, 1)
    assert _parse_date("Jul 1, 2026") == dt.date(2026, 7, 1)
    assert _parse_date("not a date") is None
