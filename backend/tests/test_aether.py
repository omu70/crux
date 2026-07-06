"""Aether AI — end-to-end API tests (deterministic mock mode, SQLite)."""
from __future__ import annotations

import os
import tempfile

os.environ["AETHER_FORCE_MOCK"] = "1"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/aether_test.db"

import pytest
from fastapi.testclient import TestClient

_db_file = os.environ["DATABASE_URL"].split("sqlite:///")[1]
if os.path.exists(_db_file):
    os.remove(_db_file)

from app.main import app  # noqa: E402
from app.core.database import SessionLocal, init_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import Campaign, Client, User  # noqa: E402


@pytest.fixture(scope="module")
def client_headers():
    init_db()
    db = SessionLocal()
    user = User(email="[email protected]", username="aether_test",
                password_hash=hash_password("test1234"), role="CLIENT")
    db.add(user)
    db.flush()
    client = Client(user_id=user.id, company_name="Glow Botanicals",
                    contact_name="Test", monthly_target_roas=2.5)
    db.add(client)
    db.flush()
    # a winner and a loser for optimizer/scoring paths
    db.add(Campaign(client_id=client.id, name="WINNER-broad", status="ACTIVE",
                    spend=500, impressions=100_000, clicks=2200, ctr=2.2, cpm=5.0,
                    cpa=12.0, conversions=42, purchase_roas=4.1, revenue=2050, frequency=1.8))
    db.add(Campaign(client_id=client.id, name="LOSER-interest", status="ACTIVE",
                    spend=400, impressions=90_000, clicks=500, ctr=0.55, cpm=4.4,
                    cpa=40.0, conversions=10, purchase_roas=0.7, revenue=280, frequency=4.6))
    db.commit()
    db.close()

    tc = TestClient(app)
    r = tc.post("/api/auth/login", json={"username": "aether_test", "password": "test1234"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return tc, {"Authorization": f"Bearer {token}"}


def test_requires_auth(client_headers):
    tc, _ = client_headers
    assert tc.get("/api/aether/business/profile").status_code == 401


def test_business_analysis(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/business/analyze", headers=h, json={
        "extra_text": "We sell organic skincare serums DTC, priced $45-80, women 28-45.",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "READY"
    assert body["summary"] and body["usp"]
    assert isinstance(body["strengths"], list)
    # profile is retrievable
    assert tc.get("/api/aether/business/profile", headers=h).status_code == 200


def test_competitors(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/competitors/discover", headers=h,
                json={"count": 3, "industry_hint": "skincare"})
    assert r.status_code == 200
    comps = tc.get("/api/aether/competitors", headers=h).json()
    assert len(comps) >= 1
    r = tc.post(f"/api/aether/competitors/{comps[0]['id']}/analyze", headers=h)
    assert r.status_code == 200
    assert r.json()["swot"] is not None


def test_personas(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/audience/generate", headers=h, json={"count": 2})
    assert r.status_code == 200
    personas = r.json()["personas"]
    assert len(personas) >= 1
    assert personas[0]["awareness_level"] in (
        "unaware", "problem_aware", "solution_aware", "product_aware", "most_aware")
    assert 1 <= personas[0]["sophistication"] <= 5


def test_creatives_generation_and_status(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/creatives/generate", headers=h,
                json={"kind": "hook", "count": 5})
    assert r.status_code == 200
    assets = r.json()
    assert len(assets) >= 1
    assert all(a["predicted_score"] > 0 for a in assets)
    r = tc.patch(f"/api/aether/creatives/{assets[0]['id']}", headers=h,
                 json={"status": "WINNER"})
    assert r.status_code == 200 and r.json()["status"] == "WINNER"
    # invalid kind rejected
    assert tc.post("/api/aether/creatives/generate", headers=h,
                   json={"kind": "nope", "count": 1}).status_code == 422


def test_visual_analysis(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/visual/analyze", headers=h,
                json={"asset_url": "https://example.com/ad.jpg", "kind": "image"})
    assert r.status_code == 200
    v = r.json()
    for k in ("creative_score", "attention_score", "scroll_stop_score", "brand_score", "emotion_score"):
        assert 0 <= v[k] <= 100
    assert v["ctr_prediction"] > 0


def test_campaign_blueprint_and_publish(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/campaigns/build", headers=h,
                json={"goal": "Scale to 3x ROAS", "daily_budget": 100})
    assert r.status_code == 200
    bp = r.json()
    assert bp["status"] == "READY" and bp["structure"]["ad_sets"]
    r = tc.post(f"/api/aether/campaigns/blueprints/{bp['id']}/publish", headers=h)
    assert r.status_code == 200
    pub = r.json()["publish_result"]
    assert pub["mode"] == "mock" and pub["campaign_id"].startswith("mock_")


def test_performance_and_scores(client_headers):
    tc, h = client_headers
    r = tc.get("/api/aether/performance/analysis?days=14", headers=h)
    assert r.status_code == 200
    assert "brief" in r.json() and "snapshot" in r.json()
    r = tc.post("/api/aether/performance/scores/generate", headers=h)
    assert r.status_code == 200
    scores = r.json()
    assert scores and 0 <= scores[0]["overall"] <= 100
    assert set(scores[0]["dimensions"]) == {
        "creative", "audience", "offer", "landing_page", "tracking", "brand", "scaling"}


def test_optimizer(client_headers):
    tc, h = client_headers
    tc.post("/api/aether/optimizer/fatigue/scan", headers=h)
    signals = tc.get("/api/aether/optimizer/fatigue", headers=h).json()
    # LOSER campaign has freq 4.6 + ctr 0.55 → must be flagged
    assert any(s["fatigue_type"] == "audience" for s in signals)
    r = tc.post("/api/aether/optimizer/budget/review", headers=h)
    assert r.status_code == 200
    actions = tc.get("/api/aether/optimizer/actions?status=PROPOSED", headers=h).json()
    assert actions
    applied = tc.post(f"/api/aether/optimizer/actions/{actions[0]['id']}/apply", headers=h)
    assert applied.status_code == 200
    # double-apply blocked
    assert tc.post(f"/api/aether/optimizer/actions/{actions[0]['id']}/apply",
                   headers=h).status_code == 409


def test_research(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/research", headers=h,
                json={"query": "skincare serum complaints", "sources": ["google"]})
    assert r.status_code == 200
    job = r.json()
    assert job["status"] in ("DONE", "FAILED")
    if job["status"] == "DONE":
        assert job["summary"]


def test_agent_council(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/agents/council", headers=h, json={
        "kind": "campaign_plan", "question": "Best structure for a $100/day launch?"})
    assert r.status_code == 200
    run = r.json()
    assert run["status"] == "DONE"
    assert run["votes"] and run["decision"]["decision"]
    assert run["decision"]["review"]["verdict"] in ("APPROVED", "REJECTED")
    # transcript retrievable
    detail = tc.get(f"/api/aether/agents/runs/{run['id']}", headers=h).json()
    assert detail["messages"]


def test_knowledge_search(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/knowledge/search", headers=h,
                json={"query": "skincare positioning"})
    assert r.status_code == 200
    hits = r.json()
    assert isinstance(hits, list) and hits, "expect hits from earlier ingested docs"
    assert "content" in hits[0] and "score" in hits[0]


def test_billing_and_usage(client_headers):
    tc, h = client_headers
    sub = tc.get("/api/aether/billing/subscription", headers=h).json()
    assert sub["plan"] == "STARTER" and sub["limits"]["competitors"] == 5
    plans = tc.get("/api/aether/billing/plans", headers=h).json()
    assert set(plans) == {"STARTER", "GROWTH", "SCALE"}
    checkout = tc.post("/api/aether/billing/checkout", headers=h,
                       json={"plan": "GROWTH"}).json()
    assert checkout["mode"] == "mock"
    assert tc.get("/api/aether/billing/subscription", headers=h).json()["plan"] == "GROWTH"
    usage = tc.get("/api/aether/usage/summary", headers=h).json()
    assert "total_cost_usd" in usage


def test_morning_report(client_headers):
    tc, h = client_headers
    r = tc.post("/api/aether/automations/morning-report", headers=h)
    assert r.status_code == 200 and r.json()["ok"]
    runs = tc.get("/api/aether/automations/runs", headers=h).json()
    assert any(x["kind"] == "morning_report" for x in runs)


def test_mock_determinism():
    from app.ai.mock import mock_embedding, mock_json
    a = mock_json("same prompt", {"hooks": ["hook"]})
    b = mock_json("same prompt", {"hooks": ["hook"]})
    assert a == b
    assert mock_embedding("hello", 64) == mock_embedding("hello", 64)


def test_creative_predictor_sanity():
    from app.ml.predictors import predict_creative
    strong = predict_creative(
        "Stop wasting money on ads that don't convert. You'll see results in 30 days — "
        "try it free today.", "hook", "PAS")
    weak = predict_creative(
        "OUR COMPANY IS THE BEST!!!! WE HAVE MANY PRODUCTS AND SERVICES FOR ALL YOUR NEEDS "
        "AND WE ARE COMMITTED TO EXCELLENCE IN EVERYTHING WE DO ALWAYS!!!!", "hook", "AIDA")
    assert strong["creative_quality"] > weak["creative_quality"]
