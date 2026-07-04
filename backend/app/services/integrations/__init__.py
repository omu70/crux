"""Marketing-platform integration clients.

Each client exposes a common surface:
    - is_configured() -> bool
    - fetch_summary() -> dict           (best-effort live pull)

Where the real API call is straightforward and safe (Meta, Shopify), we issue
it with httpx. For Google (GA4 / Search Console) and WooCommerce we ship a
documented client scaffold with the exact request shape so you only need to drop
in credentials. All clients degrade gracefully: without credentials they return
{"configured": False} rather than raising.

NOTE: Per the current setup, client performance data is entered/uploaded by the
admin (see admin routes). These clients are the drop-in path for later
automation once each client's API keys are supplied.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class BaseIntegration:
    name = "base"

    def is_configured(self) -> bool:  # pragma: no cover - overridden
        return False

    def fetch_summary(self) -> dict[str, Any]:  # pragma: no cover - overridden
        return {"configured": self.is_configured()}


class MetaAdsClient(BaseIntegration):
    """Meta Marketing API — insights endpoint."""
    name = "meta_ads"
    BASE = "https://graph.facebook.com/v19.0"

    def __init__(self, ad_account_id: str | None = None, access_token: str | None = None):
        self.ad_account_id = ad_account_id
        self.access_token = access_token or settings.META_ACCESS_TOKEN

    def is_configured(self) -> bool:
        return bool(self.ad_account_id and self.access_token)

    def fetch_summary(self) -> dict[str, Any]:
        if not self.is_configured():
            return {"configured": False, "provider": self.name}
        fields = "spend,reach,frequency,ctr,clicks,impressions,cpm,actions,purchase_roas"
        url = f"{self.BASE}/act_{self.ad_account_id}/insights"
        params = {"fields": fields, "date_preset": "last_30d", "access_token": self.access_token}
        try:
            r = httpx.get(url, params=params, timeout=20)
            r.raise_for_status()
            return {"configured": True, "provider": self.name, "data": r.json().get("data", [])}
        except Exception as exc:  # pragma: no cover - network
            return {"configured": True, "provider": self.name, "error": str(exc)}


class ShopifyClient(BaseIntegration):
    """Shopify Admin REST API — orders + shop."""
    name = "shopify"

    def __init__(self, store_domain: str | None = None, admin_token: str | None = None):
        self.store_domain = store_domain or settings.SHOPIFY_STORE_DOMAIN
        self.admin_token = admin_token or settings.SHOPIFY_ADMIN_TOKEN

    def is_configured(self) -> bool:
        return bool(self.store_domain and self.admin_token)

    def fetch_summary(self) -> dict[str, Any]:
        if not self.is_configured():
            return {"configured": False, "provider": self.name}
        url = f"https://{self.store_domain}/admin/api/2024-10/orders.json?status=any&limit=50"
        headers = {"X-Shopify-Access-Token": self.admin_token}
        try:
            r = httpx.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            orders = r.json().get("orders", [])
            revenue = sum(float(o.get("total_price", 0)) for o in orders)
            return {"configured": True, "provider": self.name, "orders": len(orders), "revenue": revenue}
        except Exception as exc:  # pragma: no cover - network
            return {"configured": True, "provider": self.name, "error": str(exc)}


class WooCommerceClient(BaseIntegration):
    """WooCommerce REST API v3 — orders."""
    name = "woocommerce"

    def __init__(self):
        self.url = settings.WOOCOMMERCE_URL
        self.key = settings.WOOCOMMERCE_KEY
        self.secret = settings.WOOCOMMERCE_SECRET

    def is_configured(self) -> bool:
        return bool(self.url and self.key and self.secret)

    def fetch_summary(self) -> dict[str, Any]:
        if not self.is_configured():
            return {"configured": False, "provider": self.name}
        try:
            r = httpx.get(
                f"{self.url.rstrip('/')}/wp-json/wc/v3/orders",
                params={"per_page": 50},
                auth=(self.key, self.secret),
                timeout=20,
            )
            r.raise_for_status()
            orders = r.json()
            revenue = sum(float(o.get("total", 0)) for o in orders)
            return {"configured": True, "provider": self.name, "orders": len(orders), "revenue": revenue}
        except Exception as exc:  # pragma: no cover - network
            return {"configured": True, "provider": self.name, "error": str(exc)}


class GA4Client(BaseIntegration):
    """Google Analytics 4 Data API scaffold.

    Requires a service account (GOOGLE_APPLICATION_CREDENTIALS) and the
    `google-analytics-data` package. Drop in credentials, then implement
    `run_report` against property `GA4_PROPERTY_ID`.
    """
    name = "ga4"

    def is_configured(self) -> bool:
        return bool(settings.GA4_PROPERTY_ID and settings.GOOGLE_APPLICATION_CREDENTIALS)

    def fetch_summary(self) -> dict[str, Any]:
        # Implementation stub — wire google.analytics.data_v1beta here.
        return {"configured": self.is_configured(), "provider": self.name}


class SearchConsoleClient(BaseIntegration):
    """Google Search Console API scaffold (searchanalytics.query)."""
    name = "search_console"

    def is_configured(self) -> bool:
        return bool(settings.SEARCH_CONSOLE_SITE_URL and settings.GOOGLE_APPLICATION_CREDENTIALS)

    def fetch_summary(self) -> dict[str, Any]:
        return {"configured": self.is_configured(), "provider": self.name}


REGISTRY = {
    "META_ADS": MetaAdsClient,
    "SHOPIFY": ShopifyClient,
    "WOOCOMMERCE": WooCommerceClient,
    "GA4": GA4Client,
    "SEARCH_CONSOLE": SearchConsoleClient,
}
