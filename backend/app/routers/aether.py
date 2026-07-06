"""Aether AI — API router. All endpoints live under /api/aether.

Interactive analyses run synchronously (they respond in mock mode instantly
and within LLM latency when keys are set); recurring work runs on Celery beat
(see app/worker.py, app/tasks/automations.py).
"""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_client
from app.models.aether import (
    AgentRun, AutomationRun, BusinessProfile, CampaignBlueprint, CampaignScore,
    CompetitorProfile, CreativeAsset, FatigueSignal, KnowledgeDocument,
    OptimizationAction, Persona, ResearchJob, UsageLedger, VisualAnalysis,
)
from app.models.models import Campaign, Client
from app.modules.audience_intel import generate_personas, serialize_persona
from app.modules.budget_optimizer import apply_action, run_budget_review, serialize_action
from app.modules.business_intel import analyze_business, serialize_profile
from app.modules.campaign_builder import build_blueprint, publish_blueprint, serialize_blueprint
from app.modules.competitor_intel import (
    analyze_competitor, discover_competitors, serialize_competitor,
)
from app.modules.creative_intel import FRAMEWORKS, KINDS, generate_creatives, serialize_asset
from app.modules.creative_optimizer import (
    auto_refresh_creatives, detect_fatigue, serialize_signal,
)
from app.modules.performance_analyst import analyze_performance
from app.modules.research_engine import SOURCES, run_research, serialize_research
from app.modules.visual_ai import analyze_visual, serialize_visual
from app.agents.orchestrator import COUNCIL_ROSTERS, run_council, run_single_agent
from app.ml.predictors import train_account_models
from app.ml.scoring import score_campaign, serialize_score
from app.rag.ingest import ingest_csv_text, ingest_pdf_bytes, ingest_text
from app.rag.store import semantic_search
from app.services import billing

router = APIRouter(prefix="/api/aether", tags=["aether"])


# ─── Schemas ──────────────────────────────────────────────────────────────────
class BusinessAnalyzeIn(BaseModel):
    website_url: str | None = None
    extra_text: str | None = None
    social_urls: list[str] = Field(default_factory=list)


class CompetitorDiscoverIn(BaseModel):
    count: int = Field(5, ge=1, le=10)
    industry_hint: str = ""


class PersonasIn(BaseModel):
    count: int = Field(4, ge=1, le=8)
    focus: str = ""


class CreativesIn(BaseModel):
    kind: str
    count: int = Field(20, ge=1, le=100)
    persona_id: str | None = None
    framework: str | None = None
    product_hint: str = ""


class VisualIn(BaseModel):
    asset_url: str
    kind: str = "image"


class BlueprintIn(BaseModel):
    goal: str
    daily_budget: float = Field(..., gt=0)
    persona_ids: list[str] = Field(default_factory=list)
    landing_url: str = ""


class ResearchIn(BaseModel):
    query: str
    sources: list[str] = Field(default_factory=list)


class CouncilIn(BaseModel):
    kind: str = "strategy_council"
    question: str
    context: str = ""


class SearchIn(BaseModel):
    query: str
    namespace: str | None = None
    k: int = Field(8, ge=1, le=25)


class CheckoutIn(BaseModel):
    plan: str
    success_url: str = "http://localhost:3000/dashboard/settings?billing=success"
    cancel_url: str = "http://localhost:3000/dashboard/settings?billing=cancel"


class StatusIn(BaseModel):
    status: str


# ─── Module 1: Business Intelligence ─────────────────────────────────────────
@router.post("/business/analyze")
def business_analyze(payload: BusinessAnalyzeIn, db: Session = Depends(get_db),
                     client: Client = Depends(get_current_client)):
    profile = analyze_business(db, client, website_url=payload.website_url,
                               extra_text=payload.extra_text, social_urls=payload.social_urls)
    return serialize_profile(profile)


@router.get("/business/profile")
def business_profile(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    p = (db.query(BusinessProfile).filter(BusinessProfile.client_id == client.id)
         .order_by(BusinessProfile.created_at.desc()).first())
    if p is None:
        raise HTTPException(404, "No business profile yet — run an analysis first")
    return serialize_profile(p)


# ─── Knowledge base / RAG ────────────────────────────────────────────────────
@router.post("/knowledge/upload")
async def knowledge_upload(file: UploadFile = File(...), namespace: str = "general",
                           db: Session = Depends(get_db),
                           client: Client = Depends(get_current_client)):
    data = await file.read()
    name = file.filename or "upload"
    if name.lower().endswith(".pdf"):
        doc = ingest_pdf_bytes(db, client.id, name, data, namespace=namespace)
    elif name.lower().endswith(".csv"):
        doc = ingest_csv_text(db, client.id, name, data.decode("utf-8", "ignore"), namespace=namespace)
    else:
        doc = ingest_text(db, client.id, name, data.decode("utf-8", "ignore")[:500_000],
                          namespace=namespace, source_type="text")
    return {"id": doc.id, "title": doc.title, "namespace": doc.namespace,
            "chunks": len(doc.chunks)}


@router.get("/knowledge/documents")
def knowledge_documents(db: Session = Depends(get_db),
                        client: Client = Depends(get_current_client)):
    docs = (db.query(KnowledgeDocument).filter(KnowledgeDocument.client_id == client.id)
            .order_by(KnowledgeDocument.created_at.desc()).limit(200).all())
    return [{"id": d.id, "title": d.title, "namespace": d.namespace,
             "source_type": d.source_type, "source_url": d.source_url,
             "created_at": d.created_at.isoformat()} for d in docs]


@router.post("/knowledge/search")
def knowledge_search(payload: SearchIn, db: Session = Depends(get_db),
                     client: Client = Depends(get_current_client)):
    return semantic_search(db, client.id, payload.query,
                           namespace=payload.namespace, k=payload.k)


# ─── Module 2: Competitor Intelligence ───────────────────────────────────────
@router.post("/competitors/discover")
def competitors_discover(payload: CompetitorDiscoverIn, db: Session = Depends(get_db),
                         client: Client = Depends(get_current_client)):
    limits = billing.plan_limits(db, client.id)
    existing = db.query(func.count(CompetitorProfile.id)).filter(
        CompetitorProfile.client_id == client.id).scalar() or 0
    cap = limits["competitors"]
    if cap != -1 and existing >= cap:
        raise HTTPException(402, f"Competitor limit reached for your plan ({cap}). Upgrade to add more.")
    created = discover_competitors(db, client, count=payload.count,
                                   industry_hint=payload.industry_hint)
    return [serialize_competitor(c) for c in created]


@router.get("/competitors")
def competitors_list(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(CompetitorProfile).filter(CompetitorProfile.client_id == client.id)
            .order_by(CompetitorProfile.created_at.desc()).all())
    return [serialize_competitor(c) for c in rows]


@router.post("/competitors/{competitor_id}/analyze")
def competitor_analyze(competitor_id: str, db: Session = Depends(get_db),
                       client: Client = Depends(get_current_client)):
    comp = db.get(CompetitorProfile, competitor_id)
    if comp is None or comp.client_id != client.id:
        raise HTTPException(404, "Competitor not found")
    return serialize_competitor(analyze_competitor(db, client, comp))


# ─── Module 3: Audience Intelligence ─────────────────────────────────────────
@router.post("/audience/generate")
def audience_generate(payload: PersonasIn, db: Session = Depends(get_db),
                      client: Client = Depends(get_current_client)):
    personas, market = generate_personas(db, client, count=payload.count, focus=payload.focus)
    return {"market": market, "personas": [serialize_persona(p) for p in personas]}


@router.get("/audience/personas")
def personas_list(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(Persona).filter(Persona.client_id == client.id)
            .order_by(Persona.created_at.desc()).all())
    return [serialize_persona(p) for p in rows]


# ─── Module 4: Creative Intelligence ─────────────────────────────────────────
@router.get("/creatives/options")
def creative_options():
    return {"kinds": KINDS, "frameworks": FRAMEWORKS}


@router.post("/creatives/generate")
def creatives_generate(payload: CreativesIn, db: Session = Depends(get_db),
                       client: Client = Depends(get_current_client)):
    if payload.kind not in KINDS:
        raise HTTPException(422, f"kind must be one of {KINDS}")
    limits = billing.plan_limits(db, client.id)
    cap = limits["creatives_per_month"]
    if cap != -1:
        month_start = dt.date.today().replace(day=1)
        used = db.query(func.count(CreativeAsset.id)).filter(
            CreativeAsset.client_id == client.id,
            CreativeAsset.created_at >= dt.datetime.combine(month_start, dt.time.min),
        ).scalar() or 0
        if used + payload.count > cap:
            raise HTTPException(402, f"Creative limit {cap}/month reached ({used} used). Upgrade your plan.")
    assets = generate_creatives(db, client, kind=payload.kind, count=payload.count,
                                persona_id=payload.persona_id, framework=payload.framework,
                                product_hint=payload.product_hint)
    return [serialize_asset(a) for a in assets]


@router.get("/creatives")
def creatives_list(kind: str | None = None, batch_id: str | None = None,
                   status: str | None = None,
                   limit: int = Query(100, le=500), offset: int = 0,
                   db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    q = db.query(CreativeAsset).filter(CreativeAsset.client_id == client.id)
    if kind:
        q = q.filter(CreativeAsset.kind == kind)
    if batch_id:
        q = q.filter(CreativeAsset.batch_id == batch_id)
    if status:
        q = q.filter(CreativeAsset.status == status)
    rows = (q.order_by(CreativeAsset.predicted_score.desc())
            .offset(offset).limit(limit).all())
    return [serialize_asset(a) for a in rows]


@router.patch("/creatives/{asset_id}")
def creative_update(asset_id: str, payload: StatusIn, db: Session = Depends(get_db),
                    client: Client = Depends(get_current_client)):
    a = db.get(CreativeAsset, asset_id)
    if a is None or a.client_id != client.id:
        raise HTTPException(404, "Creative not found")
    if payload.status not in ("DRAFT", "APPROVED", "IN_USE", "RETIRED", "WINNER"):
        raise HTTPException(422, "Invalid status")
    a.status = payload.status
    db.commit()
    return serialize_asset(a)


# ─── Module 5: Visual AI ─────────────────────────────────────────────────────
@router.post("/visual/analyze")
def visual_analyze(payload: VisualIn, db: Session = Depends(get_db),
                   client: Client = Depends(get_current_client)):
    return serialize_visual(analyze_visual(db, client, payload.asset_url, payload.kind))


@router.get("/visual")
def visual_list(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(VisualAnalysis).filter(VisualAnalysis.client_id == client.id)
            .order_by(VisualAnalysis.created_at.desc()).limit(100).all())
    return [serialize_visual(v) for v in rows]


# ─── Module 6: Campaign Builder ──────────────────────────────────────────────
@router.post("/campaigns/build")
def campaigns_build(payload: BlueprintIn, db: Session = Depends(get_db),
                    client: Client = Depends(get_current_client)):
    bp = build_blueprint(db, client, goal=payload.goal, daily_budget=payload.daily_budget,
                         persona_ids=payload.persona_ids, landing_url=payload.landing_url)
    return serialize_blueprint(bp)


@router.get("/campaigns/blueprints")
def blueprints_list(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(CampaignBlueprint).filter(CampaignBlueprint.client_id == client.id)
            .order_by(CampaignBlueprint.created_at.desc()).all())
    return [serialize_blueprint(b) for b in rows]


@router.get("/campaigns/blueprints/{bp_id}")
def blueprint_detail(bp_id: str, db: Session = Depends(get_db),
                     client: Client = Depends(get_current_client)):
    bp = db.get(CampaignBlueprint, bp_id)
    if bp is None or bp.client_id != client.id:
        raise HTTPException(404, "Blueprint not found")
    return serialize_blueprint(bp)


@router.post("/campaigns/blueprints/{bp_id}/publish")
def blueprint_publish(bp_id: str, db: Session = Depends(get_db),
                      client: Client = Depends(get_current_client)):
    bp = db.get(CampaignBlueprint, bp_id)
    if bp is None or bp.client_id != client.id:
        raise HTTPException(404, "Blueprint not found")
    try:
        result = publish_blueprint(db, client, bp)
    except Exception as exc:
        raise HTTPException(502, f"Publish failed: {exc}")
    return {"blueprint": serialize_blueprint(bp), "publish_result": result}


# ─── Module 7: Performance Analyst + scoring ─────────────────────────────────
@router.get("/performance/analysis")
def performance_analysis(days: int = Query(14, ge=7, le=90), db: Session = Depends(get_db),
                         client: Client = Depends(get_current_client)):
    return analyze_performance(db, client, days=days)


@router.post("/performance/scores/generate")
def scores_generate(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    campaigns = (db.query(Campaign).filter(Campaign.client_id == client.id)
                 .order_by(Campaign.spend.desc()).limit(10).all())
    return [serialize_score(score_campaign(db, client, c)) for c in campaigns]


@router.get("/performance/scores")
def scores_list(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(CampaignScore).filter(CampaignScore.client_id == client.id)
            .order_by(CampaignScore.date.desc()).limit(50).all())
    return [serialize_score(s) for s in rows]


# ─── Modules 8 & 9: Optimization ─────────────────────────────────────────────
@router.post("/optimizer/fatigue/scan")
def fatigue_scan(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    return [serialize_signal(s) for s in detect_fatigue(db, client)]


@router.get("/optimizer/fatigue")
def fatigue_list(include_resolved: bool = False, db: Session = Depends(get_db),
                 client: Client = Depends(get_current_client)):
    q = db.query(FatigueSignal).filter(FatigueSignal.client_id == client.id)
    if not include_resolved:
        q = q.filter(FatigueSignal.resolved.is_(False))
    return [serialize_signal(s) for s in q.order_by(FatigueSignal.created_at.desc()).limit(100).all()]


@router.post("/optimizer/fatigue/{signal_id}/refresh")
def fatigue_refresh(signal_id: str, db: Session = Depends(get_db),
                    client: Client = Depends(get_current_client)):
    sig = db.get(FatigueSignal, signal_id)
    if sig is None or sig.client_id != client.id:
        raise HTTPException(404, "Signal not found")
    return auto_refresh_creatives(db, client, sig)


@router.post("/optimizer/budget/review")
def budget_review(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    return [serialize_action(a) for a in run_budget_review(db, client)]


@router.get("/optimizer/actions")
def actions_list(status: str | None = None, db: Session = Depends(get_db),
                 client: Client = Depends(get_current_client)):
    q = db.query(OptimizationAction).filter(OptimizationAction.client_id == client.id)
    if status:
        q = q.filter(OptimizationAction.status == status.upper())
    return [serialize_action(a) for a in
            q.order_by(OptimizationAction.created_at.desc()).limit(100).all()]


@router.post("/optimizer/actions/{action_id}/apply")
def action_apply(action_id: str, db: Session = Depends(get_db),
                 client: Client = Depends(get_current_client)):
    a = db.get(OptimizationAction, action_id)
    if a is None or a.client_id != client.id:
        raise HTTPException(404, "Action not found")
    if a.status == "APPLIED":
        raise HTTPException(409, "Action already applied")
    return {"action": serialize_action(a), "result": apply_action(db, client, a)}


@router.post("/optimizer/actions/{action_id}/dismiss")
def action_dismiss(action_id: str, db: Session = Depends(get_db),
                   client: Client = Depends(get_current_client)):
    a = db.get(OptimizationAction, action_id)
    if a is None or a.client_id != client.id:
        raise HTTPException(404, "Action not found")
    a.status = "DISMISSED"
    db.commit()
    return serialize_action(a)


# ─── Module 10: Research Engine ──────────────────────────────────────────────
@router.get("/research/sources")
def research_sources():
    return {"sources": SOURCES}


@router.post("/research")
def research_run(payload: ResearchIn, db: Session = Depends(get_db),
                 client: Client = Depends(get_current_client)):
    limits = billing.plan_limits(db, client.id)
    cap = limits["research_jobs_per_month"]
    if cap != -1:
        month_start = dt.datetime.combine(dt.date.today().replace(day=1), dt.time.min)
        used = db.query(func.count(ResearchJob.id)).filter(
            ResearchJob.client_id == client.id, ResearchJob.created_at >= month_start).scalar() or 0
        if used >= cap:
            raise HTTPException(402, f"Research limit {cap}/month reached. Upgrade your plan.")
    return serialize_research(run_research(db, client, payload.query, payload.sources or None))


@router.get("/research")
def research_list(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(ResearchJob).filter(ResearchJob.client_id == client.id)
            .order_by(ResearchJob.created_at.desc()).limit(50).all())
    return [serialize_research(j) for j in rows]


@router.get("/research/{job_id}")
def research_detail(job_id: str, db: Session = Depends(get_db),
                    client: Client = Depends(get_current_client)):
    j = db.get(ResearchJob, job_id)
    if j is None or j.client_id != client.id:
        raise HTTPException(404, "Research job not found")
    return serialize_research(j)


# ─── Multi-agent council ─────────────────────────────────────────────────────
@router.get("/agents/rosters")
def agent_rosters():
    return COUNCIL_ROSTERS


@router.post("/agents/council")
def agents_council(payload: CouncilIn, db: Session = Depends(get_db),
                   client: Client = Depends(get_current_client)):
    limits = billing.plan_limits(db, client.id)
    cap = limits["councils_per_month"]
    if cap != -1:
        month_start = dt.datetime.combine(dt.date.today().replace(day=1), dt.time.min)
        used = db.query(func.count(AgentRun.id)).filter(
            AgentRun.client_id == client.id, AgentRun.created_at >= month_start,
            AgentRun.kind.in_(list(COUNCIL_ROSTERS.keys()))).scalar() or 0
        if used >= cap:
            raise HTTPException(402, f"Council limit {cap}/month reached. Upgrade your plan.")
    run = run_council(db, client.id, payload.kind, payload.question, payload.context)
    return _serialize_run(run)


@router.get("/agents/runs")
def agent_runs(kind: str | None = None, db: Session = Depends(get_db),
               client: Client = Depends(get_current_client)):
    q = db.query(AgentRun).filter(AgentRun.client_id == client.id)
    if kind:
        q = q.filter(AgentRun.kind == kind)
    rows = q.order_by(AgentRun.created_at.desc()).limit(50).all()
    return [_serialize_run(r, include_transcript=False) for r in rows]


@router.get("/agents/runs/{run_id}")
def agent_run_detail(run_id: str, db: Session = Depends(get_db),
                     client: Client = Depends(get_current_client)):
    r = db.get(AgentRun, run_id)
    if r is None or r.client_id != client.id:
        raise HTTPException(404, "Run not found")
    return _serialize_run(r)


def _serialize_run(r: AgentRun, include_transcript: bool = True) -> dict:
    out = {
        "id": r.id, "kind": r.kind, "status": r.status, "input": r.input,
        "votes": r.votes, "decision": r.decision, "error": r.error,
        "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
        "cost_usd": r.cost_usd,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "created_at": r.created_at.isoformat(),
    }
    if include_transcript:
        out["steps"] = r.steps
        out["messages"] = r.messages
    return out


# ─── ML, usage, automations ──────────────────────────────────────────────────
@router.post("/ml/train")
def ml_train(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    return train_account_models(db, client.id)


@router.get("/usage/summary")
def usage_summary(days: int = Query(30, ge=1, le=180), db: Session = Depends(get_db),
                  client: Client = Depends(get_current_client)):
    since = dt.date.today() - dt.timedelta(days=days)
    rows = (db.query(UsageLedger.provider, UsageLedger.kind,
                     func.sum(UsageLedger.tokens_in), func.sum(UsageLedger.tokens_out),
                     func.sum(UsageLedger.cost_usd))
            .filter(UsageLedger.client_id == client.id, UsageLedger.date >= since)
            .group_by(UsageLedger.provider, UsageLedger.kind).all())
    return {
        "days": days,
        "by_provider": [{"provider": p, "kind": k, "tokens_in": int(ti or 0),
                         "tokens_out": int(to or 0), "cost_usd": round(float(c or 0), 4)}
                        for p, k, ti, to, c in rows],
        "total_cost_usd": round(sum(float(c or 0) for *_, c in rows), 4),
    }


@router.get("/automations/runs")
def automation_runs(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(AutomationRun)
            .filter((AutomationRun.client_id == client.id) | (AutomationRun.client_id.is_(None)))
            .order_by(AutomationRun.created_at.desc()).limit(60).all())
    return [{"id": r.id, "kind": r.kind, "status": r.status, "output": r.output,
             "created_at": r.created_at.isoformat()} for r in rows]


@router.post("/automations/morning-report")
def trigger_morning_report(db: Session = Depends(get_db),
                           client: Client = Depends(get_current_client)):
    from app.tasks.automations import morning_briefing_for
    return morning_briefing_for(client.id)


# ─── Billing ─────────────────────────────────────────────────────────────────
@router.get("/billing/plans")
def billing_plans():
    return billing.PLANS


@router.get("/billing/subscription")
def billing_subscription(db: Session = Depends(get_db),
                         client: Client = Depends(get_current_client)):
    return billing.serialize_subscription(billing.get_or_create_subscription(db, client.id))


@router.post("/billing/checkout")
def billing_checkout(payload: CheckoutIn, db: Session = Depends(get_db),
                     client: Client = Depends(get_current_client)):
    try:
        return billing.create_checkout_session(db, client.id, payload.plan,
                                               payload.success_url, payload.cancel_url)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post("/billing/webhook", include_in_schema=False)
async def billing_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        return billing.handle_webhook(db, payload, signature)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
