"""Client marketing data: Meta Ads, e-commerce, analytics, search console, SEO."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_client
from app.models import (
    AnalyticsSnapshot, Campaign, Client, Order, Product, SearchConsoleSnapshot, SeoSnapshot,
)

router = APIRouter(prefix="/api/marketing", tags=["marketing"])


@router.get("/campaigns")
def campaigns(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = db.query(Campaign).filter(Campaign.client_id == client.id).all()
    def dump(c: Campaign):
        return {k: getattr(c, k) for k in (
            "id", "name", "status", "objective", "spend", "reach", "frequency", "ctr",
            "clicks", "impressions", "cpm", "cpa", "conversions", "purchase_roas",
            "revenue", "is_winning", "is_losing")}
    data = [dump(c) for c in rows]
    return {
        "campaigns": data,
        "summary": {
            "active": sum(1 for c in rows if c.status == "ACTIVE"),
            "paused": sum(1 for c in rows if c.status == "PAUSED"),
            "rejected": sum(1 for c in rows if c.status == "REJECTED"),
            "learning": sum(1 for c in rows if c.status == "LEARNING"),
            "winning": next((c.name for c in rows if c.is_winning), None),
            "losing": next((c.name for c in rows if c.is_losing), None),
            "total_spend": round(sum(c.spend for c in rows), 2),
            "total_revenue": round(sum(c.revenue for c in rows), 2),
        },
    }


@router.get("/ecommerce")
def ecommerce(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    orders = db.query(Order).filter(Order.client_id == client.id).all()
    products = db.query(Product).filter(Product.client_id == client.id).all()
    paid = [o for o in orders if o.status == "PAID"]
    revenue = sum(o.total for o in paid)
    top_products = sorted(products, key=lambda p: p.revenue, reverse=True)[:5]
    categories: dict[str, float] = {}
    for p in products:
        categories[p.category] = categories.get(p.category, 0) + p.revenue
    return {
        "orders": len(orders),
        "revenue": round(revenue, 2),
        "cancelled": sum(1 for o in orders if o.status == "CANCELLED"),
        "refunds": sum(1 for o in orders if o.status == "REFUNDED"),
        "aov": round(revenue / len(paid), 2) if paid else 0,
        "top_products": [{"title": p.title, "revenue": p.revenue, "units_sold": p.units_sold} for p in top_products],
        "top_categories": sorted(
            [{"category": k, "revenue": round(v, 2)} for k, v in categories.items()],
            key=lambda x: x["revenue"], reverse=True),
        "inventory_alerts": [{"title": p.title, "inventory": p.inventory}
                             for p in products if p.low_stock],
        "recent_orders": [{"order_number": o.order_number, "customer_name": o.customer_name,
                           "total": o.total, "status": o.status, "created_at": o.created_at.isoformat()}
                          for o in sorted(orders, key=lambda o: o.created_at, reverse=True)[:10]],
    }


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    row = (db.query(AnalyticsSnapshot)
           .filter(AnalyticsSnapshot.client_id == client.id)
           .order_by(AnalyticsSnapshot.date.desc()).first())
    if row is None:
        return {}
    return {
        "date": row.date.isoformat(),
        "visitors": row.visitors, "sessions": row.sessions,
        "bounce_rate": row.bounce_rate, "engagement_time": row.engagement_time,
        "traffic_sources": {"organic": row.organic, "paid": row.paid,
                            "direct": row.direct, "referral": row.referral},
        "top_countries": row.top_countries or [], "top_cities": row.top_cities or [],
        "devices": row.devices or [], "browsers": row.browsers or [],
    }


@router.get("/search-console")
def search_console(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    row = (db.query(SearchConsoleSnapshot)
           .filter(SearchConsoleSnapshot.client_id == client.id)
           .order_by(SearchConsoleSnapshot.date.desc()).first())
    if row is None:
        return {}
    return {
        "date": row.date.isoformat(),
        "clicks": row.clicks, "impressions": row.impressions,
        "avg_position": row.avg_position, "ctr": row.ctr,
        "top_keywords": row.top_keywords or [], "top_pages": row.top_pages or [],
    }


@router.get("/seo")
def seo(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    row = (db.query(SeoSnapshot)
           .filter(SeoSnapshot.client_id == client.id)
           .order_by(SeoSnapshot.date.desc()).first())
    if row is None:
        return {}
    return {
        "date": row.date.isoformat(),
        "keyword_growth": row.keyword_growth, "backlinks": row.backlinks,
        "indexed_pages": row.indexed_pages, "technical_issues": row.technical_issues,
        "suggestions": row.suggestions or [],
    }
