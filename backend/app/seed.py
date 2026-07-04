"""Seed CRUX with a realistic, fully-explorable demo dataset.

Run with:  python -m app.seed
Idempotent: if the admin user already exists the script exits without changes.
"""
from __future__ import annotations

import datetime as dt
import random

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models import (
    AccountManager, AiInsight, Alert, AnalyticsSnapshot, Announcement, Campaign,
    ChatMessage, Client, Document, Goal, Integration, MeetingNote, MetricSnapshot,
    Notification, Order, PerformanceScore, Product, Report, SearchConsoleSnapshot,
    SeoSnapshot, Task, Ticket, TicketMessage, User, WebsiteHealth,
)

random.seed(42)
TODAY = dt.date.today()


def _metrics_for(client_id: str, days: int, base_rev: float, base_spend: float):
    rows = []
    for i in range(days):
        date = TODAY - dt.timedelta(days=days - 1 - i)
        growth = 1 + (i / days) * 0.35                      # upward trend
        noise = random.uniform(0.82, 1.18)
        weekend = 0.8 if date.weekday() >= 5 else 1.0
        revenue = round(base_rev * growth * noise * weekend, 2)
        ad_spend = round(base_spend * growth * random.uniform(0.9, 1.1), 2)
        orders = max(1, int(revenue / random.uniform(55, 85)))
        conversions = max(1, int(orders * random.uniform(0.9, 1.1)))
        clicks = int(ad_spend / random.uniform(0.4, 0.8))
        impressions = int(clicks / random.uniform(0.012, 0.02))
        reach = int(impressions / random.uniform(1.2, 1.8))
        rows.append(MetricSnapshot(
            client_id=client_id, date=date, revenue=revenue, orders=orders, ad_spend=ad_spend,
            roas=round(revenue / ad_spend, 2) if ad_spend else 0,
            ctr=round(clicks / impressions * 100, 2) if impressions else 0,
            cpa=round(ad_spend / conversions, 2) if conversions else 0,
            cpm=round(ad_spend / impressions * 1000, 2) if impressions else 0,
            conversion_rate=round(conversions / clicks * 100, 2) if clicks else 0,
            aov=round(revenue / orders, 2) if orders else 0,
            revenue_growth=round((growth - 1) * 100, 1),
            sessions=int(clicks * random.uniform(1.4, 2.0)),
            returning_customers=int(orders * random.uniform(0.25, 0.4)),
            new_customers=int(orders * random.uniform(0.6, 0.75)),
            profit_estimate=round(revenue * random.uniform(0.28, 0.42) - ad_spend, 2),
            lead_count=int(orders * random.uniform(1.5, 2.5)),
            whatsapp_leads=int(orders * random.uniform(0.4, 0.8)),
            phone_calls=int(orders * random.uniform(0.2, 0.5)),
            impressions=impressions, clicks=clicks, reach=reach,
        ))
    return rows


def _seed_client(db: Session, *, company: str, contact: str, username: str, email: str,
                 plan: str, budget: float, manager: AccountManager, base_rev: float, base_spend: float):
    user = User(email=email, username=username, password_hash=hash_password("Client@12345"),
                role="CLIENT", is_active=True)
    db.add(user)
    db.flush()

    client = Client(
        user_id=user.id, company_name=company, contact_name=contact, plan=plan,
        monthly_budget=budget, monthly_target_revenue=base_rev * 34,
        monthly_target_roas=4.5, monthly_target_leads=520,
        account_manager_id=manager.id, currency="USD",
    )
    db.add(client)
    db.flush()
    cid = client.id

    # Integrations
    for typ, name, status in [
        ("META_ADS", f"{company} Ad Account", "CONNECTED"),
        ("SHOPIFY", f"{username}.myshopify.com", "CONNECTED"),
        ("GA4", "GA4 Property", "CONNECTED"),
        ("SEARCH_CONSOLE", "sc-domain:"+username+".com", "CONNECTED"),
        ("CLARITY", "Clarity Project", "PENDING"),
    ]:
        db.add(Integration(client_id=cid, type=typ, account_name=name, status=status,
                           last_synced_at=dt.datetime.now(dt.timezone.utc)))

    # 90 days of metrics
    db.add_all(_metrics_for(cid, 90, base_rev, base_spend))

    # Campaigns
    camp_defs = [
        ("Summer Sale — Advantage+", "ACTIVE", 4820, 5.1, True, False),
        ("Retargeting — Add To Cart", "ACTIVE", 2110, 6.4, False, False),
        ("Prospecting — Broad", "LEARNING", 1560, 2.1, False, False),
        ("Brand Awareness — Reels", "PAUSED", 640, 1.4, False, True),
        ("Catalog Sales — DPA", "ACTIVE", 3050, 4.8, False, False),
        ("Lookalike 1% — Purchases", "REJECTED", 0, 0, False, False),
    ]
    for name, status, spend, roas, win, lose in camp_defs:
        conv = int(spend * roas / random.uniform(55, 80)) if spend else 0
        clicks = int(spend / random.uniform(0.4, 0.7)) if spend else 0
        impr = int(clicks / 0.015) if clicks else 0
        db.add(Campaign(
            client_id=cid, name=name, status=status, spend=spend, revenue=round(spend * roas, 2),
            purchase_roas=roas, conversions=conv, clicks=clicks, impressions=impr,
            reach=int(impr / 1.5) if impr else 0, frequency=round(random.uniform(1.1, 2.4), 2),
            ctr=round(clicks / impr * 100, 2) if impr else 0,
            cpm=round(spend / impr * 1000, 2) if impr else 0,
            cpa=round(spend / conv, 2) if conv else 0, is_winning=win, is_losing=lose,
        ))

    # Orders
    names = ["Ava Patel", "Liam Chen", "Noah Kim", "Mia Garcia", "Ethan Brown", "Zoe Ali",
             "Lucas Meyer", "Emma Rossi", "Kai Nakamura", "Sara Haddad"]
    statuses = ["PAID"] * 8 + ["CANCELLED", "REFUNDED"]
    for i in range(40):
        db.add(Order(
            client_id=cid, order_number=f"#{1000 + i}", customer_name=random.choice(names),
            total=round(random.uniform(35, 260), 2), status=random.choice(statuses),
            items_count=random.randint(1, 4),
            created_at=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=random.randint(0, 29)),
        ))

    # Products
    prod_defs = [("Aurora Serum", "Skincare", 48), ("Velvet Cleanser", "Skincare", 32),
                 ("Hydra Mist", "Skincare", 24), ("Glow Kit", "Bundles", 89),
                 ("Night Repair Oil", "Skincare", 56), ("Travel Set", "Bundles", 39)]
    for title, cat, price in prod_defs:
        units = random.randint(40, 320)
        inv = random.randint(0, 120)
        db.add(Product(client_id=cid, title=title, category=cat, price=price, units_sold=units,
                       revenue=round(units * price, 2), inventory=inv, low_stock=inv < 15))

    # Analytics
    db.add(AnalyticsSnapshot(
        client_id=cid, date=TODAY, visitors=random.randint(8000, 20000),
        sessions=random.randint(12000, 30000), bounce_rate=round(random.uniform(38, 52), 1),
        engagement_time=round(random.uniform(75, 140), 1),
        organic=random.randint(30, 45), paid=random.randint(25, 40),
        direct=random.randint(10, 20), referral=random.randint(5, 15),
        top_countries=[{"country": c, "sessions": random.randint(1000, 9000)}
                       for c in ["United States", "United Kingdom", "Canada", "Australia", "Germany"]],
        top_cities=[{"city": c, "sessions": random.randint(500, 4000)}
                    for c in ["New York", "London", "Toronto", "Sydney", "Berlin"]],
        devices=[{"device": "Mobile", "share": 63}, {"device": "Desktop", "share": 31}, {"device": "Tablet", "share": 6}],
        browsers=[{"browser": "Chrome", "share": 58}, {"browser": "Safari", "share": 27}, {"browser": "Edge", "share": 9}, {"browser": "Firefox", "share": 6}],
    ))

    # Search console
    db.add(SearchConsoleSnapshot(
        client_id=cid, date=TODAY, clicks=random.randint(3000, 9000),
        impressions=random.randint(80000, 200000), avg_position=round(random.uniform(6.5, 14), 1),
        ctr=round(random.uniform(2.4, 5.1), 2),
        top_keywords=[{"keyword": k, "clicks": random.randint(80, 900), "position": round(random.uniform(1, 12), 1)}
                      for k in ["vitamin c serum", "best cleanser", "glow skincare", "night oil", "hydrating mist"]],
        top_pages=[{"page": p, "clicks": random.randint(120, 1400)}
                   for p in ["/products/aurora-serum", "/collections/bestsellers", "/blog/skincare-routine", "/products/glow-kit"]],
    ))

    # SEO
    db.add(SeoSnapshot(client_id=cid, date=TODAY, keyword_growth=round(random.uniform(8, 24), 1),
                       backlinks=random.randint(400, 2200), indexed_pages=random.randint(120, 480),
                       technical_issues=random.randint(2, 14),
                       suggestions=["Fix 4 broken internal links", "Add alt text to 12 product images",
                                    "Improve LCP on collection pages", "Publish 2 blog posts targeting long-tail terms"]))

    # Report
    db.add(Report(
        client_id=cid, title=f"{TODAY.strftime('%B %Y')} Performance Report", month=TODAY.strftime("%B %Y"),
        summary=f"{company} delivered strong month-over-month growth with blended ROAS up and CPA trending down. "
                "Meta remained the primary revenue driver, with retargeting posting the highest efficiency.",
        wins=["Revenue up 23% MoM", "ROAS improved to 4.6x", "Retargeting CPA down 18%"],
        losses=["Brand Awareness campaign under-delivered", "Mobile bounce rate ticked up"],
        kpis={"revenue": base_rev * 34, "roas": 4.6, "orders": 1120, "cpa": 22.4},
        suggestions=["Scale Advantage+ by 20%", "Pause Brand Awareness — Reels", "Launch Add-To-Cart retargeting flow"],
        strategy="Next month: double down on catalog sales, expand lookalikes, and test UGC creative angles.",
        created_by="admin",
    ))

    # Tasks
    task_defs = [
        ("Launch Advantage+ Shopping campaign", "IN_PROGRESS", "HIGH", "today", "Sarah (Media Buyer)"),
        ("Refresh top-of-funnel creatives", "PENDING", "HIGH", "week", "Design Team"),
        ("Fix broken internal links (SEO)", "PENDING", "MEDIUM", "week", "Dev Team"),
        ("Set up Add-To-Cart retargeting flow", "IN_PROGRESS", "MEDIUM", "week", "Sarah (Media Buyer)"),
        ("Publish 2 SEO blog posts", "PENDING", "LOW", "month", "Content Team"),
        ("Monthly reporting call", "COMPLETED", "MEDIUM", "month", "Account Manager"),
    ]
    for title, status, prio, tf, resp in task_defs:
        db.add(Task(client_id=cid, title=title, status=status, priority=prio, timeframe=tf,
                    responsible=resp, expected_result="Improve efficiency and scale profitable spend",
                    due_date=dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=random.randint(1, 21))))

    # Goals
    db.add_all([
        Goal(client_id=cid, type="REVENUE", label="Monthly Revenue Goal", target=base_rev * 34,
             current=base_rev * 34 * random.uniform(0.55, 0.8), unit="$", period="month"),
        Goal(client_id=cid, type="ROAS", label="Monthly ROAS Goal", target=4.5,
             current=round(random.uniform(3.8, 4.6), 2), unit="x", period="month"),
        Goal(client_id=cid, type="LEADS", label="Lead Goal", target=520,
             current=random.randint(300, 480), unit="", period="month"),
        Goal(client_id=cid, type="SALES", label="Sales Goal", target=1200,
             current=random.randint(700, 1100), unit="", period="month"),
    ])

    # Meeting notes
    db.add(MeetingNote(client_id=cid, title="Monthly Strategy Sync", notes="Reviewed performance, aligned on scaling plan and creative refresh.",
                       action_items=["Send new creative brief", "Approve +20% budget", "Share competitor analysis"],
                       meeting_date=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=5)))

    # Notifications
    for typ, title, msg in [
        ("CAMPAIGN_APPROVED", "Campaign approved", "Summer Sale — Advantage+ is now live."),
        ("CREATIVE_UPLOADED", "New creatives uploaded", "5 new video creatives added to your library."),
        ("BUDGET_INCREASED", "Budget increased", "Daily budget raised by 20% on top campaign."),
        ("MEETING_SCHEDULED", "Meeting scheduled", "Monthly strategy call booked for next Tuesday."),
        ("REPORT_READY", "Report ready", "Your monthly performance report is available."),
    ]:
        db.add(Notification(client_id=cid, type=typ, title=title, message=msg,
                            read=random.choice([True, False])))

    # Documents
    for name, cat, ftype in [("Invoice-July.pdf", "INVOICE", "pdf"), ("Monthly-Report.pdf", "REPORT", "pdf"),
                             ("Q3-Contract.pdf", "CONTRACT", "pdf"), ("Ad-Creative-Pack.zip", "CREATIVE", "zip")]:
        db.add(Document(client_id=cid, name=name, category=cat, file_type=ftype,
                        file_url=f"/uploads/sample-{name}", size_bytes=random.randint(50_000, 4_000_000),
                        uploaded_by="admin"))

    # Ticket + message
    ticket = Ticket(client_id=cid, subject="Question about last week's ROAS dip",
                    description="Noticed ROAS dropped on Thursday — can we review the ad set?", priority="MEDIUM", status="OPEN")
    db.add(ticket)
    db.flush()
    db.add(TicketMessage(ticket_id=ticket.id, sender_id=user.id, body="Noticed ROAS dropped on Thursday — can we review?"))

    # Chat
    db.add_all([
        ChatMessage(client_id=cid, sender_id=user.id, sender_role="CLIENT", body="Hey team, loving the new dashboard!"),
    ])

    # Alerts
    db.add_all([
        Alert(client_id=cid, type="ROAS_DROP", severity="WARNING", title="ROAS dropped 8%",
              message="Blended ROAS fell below your 4.5x target over the last 3 days."),
        Alert(client_id=cid, type="SHOPIFY_DISCONNECTED", severity="INFO", title="Clarity not connected",
              message="Connect Microsoft Clarity to unlock heatmaps."),
    ])

    # Performance score + website health
    db.add(PerformanceScore(client_id=cid, date=TODAY, overall=random.randint(74, 92),
                            ads_score=random.randint(70, 95), seo_score=random.randint(60, 88),
                            website_score=random.randint(72, 94), revenue_score=random.randint(75, 96),
                            speed_score=random.randint(65, 90), conversion_score=random.randint(68, 90)))
    db.add(WebsiteHealth(client_id=cid, date=TODAY, performance=random.randint(72, 96),
                         accessibility=random.randint(85, 99), seo=random.randint(80, 97),
                         best_practices=random.randint(83, 100), lcp=round(random.uniform(1.8, 3.2), 2),
                         fid=round(random.uniform(8, 40), 1), cls=round(random.uniform(0.02, 0.14), 3)))

    # AI insights (persisted)
    from app.services.ai import generate_insights
    metric_dicts = [{"revenue": m.revenue, "roas": m.roas, "ctr": m.ctr, "cpa": m.cpa,
                     "conversion_rate": m.conversion_rate} for m in _metrics_for(cid, 14, base_rev, base_spend)]
    for ins in generate_insights(company, metric_dicts):
        db.add(AiInsight(client_id=cid, title=ins["title"], body=ins["body"],
                         category=ins.get("category", "performance"), impact=ins.get("impact", "MEDIUM")))

    return client


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == settings.SEED_ADMIN_USERNAME).first():
            print("• Seed skipped — admin user already exists.")
            return

        admin = User(email=settings.SEED_ADMIN_EMAIL, username=settings.SEED_ADMIN_USERNAME,
                     password_hash=hash_password(settings.SEED_ADMIN_PASSWORD), role="ADMIN", is_active=True)
        db.add(admin)
        db.commit()  # commit admin first so login always works, even if demo data fails
        print(f"✓ Admin ready → username: {settings.SEED_ADMIN_USERNAME}  password: {settings.SEED_ADMIN_PASSWORD}")

        try:
            m1 = AccountManager(name="Priya Sharma", email="[email protected]", title="Senior Account Manager")
            m2 = AccountManager(name="Daniel Okoro", email="[email protected]", title="Growth Strategist")
            db.add_all([m1, m2])
            db.flush()

            db.add(Announcement(title="Welcome to CRUX ✨", message="Your new client portal is live. Explore your dashboard!", created_by="admin"))

            _seed_client(db, company="Lumina Skincare", contact="Jordan Lee", username="lumina", email="[email protected]",
                         plan="Scale", budget=25000, manager=m1, base_rev=4200, base_spend=980)
            _seed_client(db, company="NorthPeak Outdoors", contact="Sam Rivera", username="northpeak", email="[email protected]",
                         plan="Growth", budget=14000, manager=m2, base_rev=2600, base_spend=620)

            db.commit()
            print("✓ Seed complete (admin + 2 demo clients).")
            print("  Client → username: lumina     password: Client@12345")
            print("  Client → username: northpeak  password: Client@12345")
        except Exception as exc:
            db.rollback()
            print(f"⚠ Demo data skipped ({exc}). Admin account is ready to use.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
