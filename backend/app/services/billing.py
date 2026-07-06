"""Stripe billing — subscriptions, checkout, webhooks, plan gating.

stripe is an optional dependency (lazy import, matching CRUX integration
conventions). Without STRIPE_SECRET_KEY the endpoints respond in mock mode so
the full upgrade flow is demo-able.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.aether import Subscription

log = logging.getLogger("aether.billing")

PLANS: dict[str, dict[str, Any]] = {
    "STARTER": {
        "name": "Starter", "price_usd": 99,
        "limits": {"creatives_per_month": 500, "councils_per_month": 10,
                   "research_jobs_per_month": 10, "competitors": 5, "seats": 2},
    },
    "GROWTH": {
        "name": "Growth", "price_usd": 299,
        "limits": {"creatives_per_month": 3000, "councils_per_month": 60,
                   "research_jobs_per_month": 60, "competitors": 15, "seats": 5},
    },
    "SCALE": {
        "name": "Scale", "price_usd": 799,
        "limits": {"creatives_per_month": -1, "councils_per_month": -1,
                   "research_jobs_per_month": -1, "competitors": -1, "seats": 15},
    },
}

_PRICE_ATTRS = {"STARTER": "STRIPE_PRICE_STARTER", "GROWTH": "STRIPE_PRICE_GROWTH",
                "SCALE": "STRIPE_PRICE_SCALE"}


def _stripe():
    if not settings.STRIPE_SECRET_KEY:
        return None
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        return stripe
    except ImportError:
        log.warning("stripe package not installed; billing in mock mode")
        return None


def get_or_create_subscription(db: Session, client_id: str) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.client_id == client_id).first()
    if sub is None:
        sub = Subscription(client_id=client_id, plan="STARTER", status="TRIALING",
                           current_period_end=dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=14))
        db.add(sub)
        db.commit()
    return sub


def plan_limits(db: Session, client_id: str) -> dict[str, Any]:
    sub = get_or_create_subscription(db, client_id)
    return PLANS.get(sub.plan, PLANS["STARTER"])["limits"]


def create_checkout_session(db: Session, client_id: str, plan: str,
                            success_url: str, cancel_url: str) -> dict[str, Any]:
    plan = plan.upper()
    if plan not in PLANS:
        raise ValueError(f"Unknown plan {plan}")
    sub = get_or_create_subscription(db, client_id)
    stripe = _stripe()
    if stripe is None:
        # Mock mode: apply the plan instantly so the flow is demo-able.
        sub.plan = plan
        sub.status = "ACTIVE"
        sub.current_period_end = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30)
        db.commit()
        return {"mode": "mock", "url": success_url,
                "note": "STRIPE_SECRET_KEY not set — plan applied directly for demo."}

    price_id = getattr(settings, _PRICE_ATTRS[plan])
    if not price_id:
        raise ValueError(f"Stripe price id for {plan} not configured")
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=client_id,
        customer=sub.stripe_customer_id or None,
        metadata={"client_id": client_id, "plan": plan},
    )
    return {"mode": "live", "url": session.url, "session_id": session.id}


def handle_webhook(db: Session, payload: bytes, signature: str) -> dict[str, Any]:
    stripe = _stripe()
    if stripe is None:
        return {"handled": False, "reason": "stripe not configured"}
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        raise ValueError(f"Invalid webhook: {exc}")

    obj = event["data"]["object"]
    etype = event["type"]

    if etype == "checkout.session.completed":
        client_id = obj.get("client_reference_id") or (obj.get("metadata") or {}).get("client_id")
        if client_id:
            sub = get_or_create_subscription(db, client_id)
            sub.stripe_customer_id = obj.get("customer")
            sub.stripe_subscription_id = obj.get("subscription")
            sub.plan = (obj.get("metadata") or {}).get("plan", sub.plan)
            sub.status = "ACTIVE"
            db.commit()
    elif etype in ("customer.subscription.updated", "customer.subscription.deleted"):
        sub = (db.query(Subscription)
               .filter(Subscription.stripe_subscription_id == obj.get("id")).first())
        if sub:
            status_map = {"active": "ACTIVE", "trialing": "TRIALING",
                          "past_due": "PAST_DUE", "canceled": "CANCELED",
                          "unpaid": "PAST_DUE"}
            sub.status = status_map.get(obj.get("status"), sub.status)
            if obj.get("current_period_end"):
                sub.current_period_end = dt.datetime.fromtimestamp(
                    obj["current_period_end"], dt.timezone.utc)
            db.commit()
    return {"handled": True, "type": etype}


def serialize_subscription(s: Subscription) -> dict[str, Any]:
    plan = PLANS.get(s.plan, PLANS["STARTER"])
    return {
        "plan": s.plan, "plan_name": plan["name"], "price_usd": plan["price_usd"],
        "status": s.status, "limits": plan["limits"],
        "current_period_end": s.current_period_end.isoformat() if s.current_period_end else None,
    }
