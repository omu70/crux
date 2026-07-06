"""Meta Marketing API publisher.

Publishes CampaignBlueprints as real (paused) campaigns/ad sets/ads via the
Graph API. Without META_ACCESS_TOKEN + META_AD_ACCOUNT_ID it runs in mock mode
and returns deterministic fake ids, so the launch flow is fully testable.

Safety: everything is created with status=PAUSED — a human (or an approved
OptimizationAction) flips things live.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any

import httpx

from app.core.config import settings

log = logging.getLogger("aether.meta")

GRAPH = "https://graph.facebook.com"


class MetaPublishError(Exception):
    pass


class MetaPublisher:
    def __init__(self) -> None:
        self.token = settings.META_ACCESS_TOKEN
        self.account = settings.META_AD_ACCOUNT_ID
        self.version = settings.META_API_VERSION

    @property
    def live(self) -> bool:
        return bool(self.token and self.account)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        r = httpx.post(
            f"{GRAPH}/{self.version}/{path}",
            data={**payload, "access_token": self.token},
            timeout=60,
        )
        if r.status_code >= 400:
            try:
                err = r.json().get("error", {})
            except Exception:
                err = {"message": r.text[:300]}
            raise MetaPublishError(f"Meta API error on {path}: {err.get('message')}")
        return r.json()

    def _mock_id(self, *parts: str) -> str:
        return "mock_" + hashlib.md5("|".join(parts).encode()).hexdigest()[:12]

    # ── public API ────────────────────────────────────────────────────────────
    def publish_blueprint(self, blueprint_name: str, structure: dict[str, Any],
                          daily_budget: float, currency: str = "USD") -> dict[str, Any]:
        """structure = {campaign:{...}, ad_sets:[{..., ads:[{...}]}]} (from the builder).
        Returns {campaign_id, ad_sets: [{id, ads: [id]}], mode}.
        """
        camp = structure.get("campaign", {})
        ad_sets = structure.get("ad_sets", [])

        if not self.live:
            return {
                "mode": "mock",
                "campaign_id": self._mock_id("campaign", blueprint_name),
                "ad_sets": [{
                    "id": self._mock_id("adset", blueprint_name, str(i)),
                    "name": a.get("name"),
                    "ads": [self._mock_id("ad", blueprint_name, str(i), str(j))
                            for j, _ in enumerate(a.get("ads", []))],
                } for i, a in enumerate(ad_sets)],
                "note": "META_ACCESS_TOKEN/META_AD_ACCOUNT_ID not set — nothing was published.",
            }

        campaign_res = self._post(f"{self.account}/campaigns", {
            "name": camp.get("name", blueprint_name),
            "objective": camp.get("objective", "OUTCOME_SALES"),
            "status": "PAUSED",
            "special_ad_categories": "[]",
            "buying_type": "AUCTION",
        })
        campaign_id = campaign_res["id"]

        out_sets = []
        n_sets = max(1, len(ad_sets))
        for aset in ad_sets:
            budget_minor = int(daily_budget / n_sets * 100)
            adset_res = self._post(f"{self.account}/adsets", {
                "name": aset.get("name", "Ad Set"),
                "campaign_id": campaign_id,
                "daily_budget": max(100, budget_minor),
                "billing_event": "IMPRESSIONS",
                "optimization_goal": aset.get("optimization_goal", "OFFSITE_CONVERSIONS"),
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                "status": "PAUSED",
                "targeting": __import__("json").dumps(aset.get("targeting", {"geo_locations": {"countries": ["US"]}})),
                **({"promoted_object": __import__("json").dumps({
                    "pixel_id": settings.META_PIXEL_ID,
                    "custom_event_type": aset.get("conversion_event", "PURCHASE"),
                })} if settings.META_PIXEL_ID else {}),
            })
            ad_ids = []
            for ad in aset.get("ads", []):
                creative_res = self._post(f"{self.account}/adcreatives", {
                    "name": f"{ad.get('name', 'Ad')} creative",
                    "object_story_spec": __import__("json").dumps({
                        "page_id": settings.META_PAGE_ID,
                        "link_data": {
                            "message": ad.get("primary_text", ""),
                            "link": ad.get("link", "https://example.com"),
                            "name": ad.get("headline", ""),
                            "call_to_action": {"type": ad.get("cta_type", "SHOP_NOW")},
                        },
                    }),
                })
                ad_res = self._post(f"{self.account}/ads", {
                    "name": ad.get("name", "Ad"),
                    "adset_id": adset_res["id"],
                    "creative": __import__("json").dumps({"creative_id": creative_res["id"]}),
                    "status": "PAUSED",
                })
                ad_ids.append(ad_res["id"])
            out_sets.append({"id": adset_res["id"], "name": aset.get("name"), "ads": ad_ids})

        return {"mode": "live", "campaign_id": campaign_id, "ad_sets": out_sets,
                "note": "Published PAUSED — review in Ads Manager, then activate."}

    def update_budget(self, adset_id: str, new_daily_budget: float) -> dict[str, Any]:
        if not self.live or adset_id.startswith("mock_"):
            return {"mode": "mock", "adset_id": adset_id, "daily_budget": new_daily_budget}
        return self._post(adset_id, {"daily_budget": int(new_daily_budget * 100)})

    def pause(self, object_id: str) -> dict[str, Any]:
        if not self.live or object_id.startswith("mock_"):
            return {"mode": "mock", "id": object_id, "status": "PAUSED"}
        return self._post(object_id, {"status": "PAUSED"})


meta_publisher = MetaPublisher()
