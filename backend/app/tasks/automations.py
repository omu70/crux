"""Scheduled automations — the "never sleeps" part.

Every morning per active client:
  1. Generate the daily performance brief (AI Performance Analyst).
  2. Detect problems (fatigue signals, losing campaigns).
  3. Produce an action plan (budget optimizer proposals).
  4. Notify the user (in-app Notification + email when Resend is configured).
"""
from __future__ import annotations

import logging
from typing import Any

from app.worker import celery_app

log = logging.getLogger("aether.automations")


def _session():
    from app.core.database import SessionLocal
    return SessionLocal()


def _active_clients(db) -> list:
    from app.models.models import Client
    return db.query(Client).filter(Client.status == "ACTIVE").all()


@celery_app.task(name="aether.morning_briefing_all")
def morning_briefing_all() -> dict[str, Any]:
    db = _session()
    try:
        results = [morning_briefing_for(c.id) for c in _active_clients(db)]
        return {"clients": len(results)}
    finally:
        db.close()


def morning_briefing_for(client_id: str) -> dict[str, Any]:
    from app.models.aether import AutomationRun, FatigueSignal, OptimizationAction
    from app.models.models import Client, Notification
    from app.modules.budget_optimizer import run_budget_review
    from app.modules.creative_optimizer import detect_fatigue
    from app.modules.performance_analyst import analyze_performance

    db = _session()
    try:
        client = db.get(Client, client_id)
        if client is None:
            return {"client_id": client_id, "skipped": True}

        analysis = analyze_performance(db, client, days=14)
        signals = detect_fatigue(db, client)
        actions = run_budget_review(db, client)

        brief = analysis.get("brief", {})
        problem_count = len(signals) + len([a for a in actions if a.action in ("kill", "decrease_budget")])
        title = f"☀️ Morning briefing: {brief.get('headline', 'account update')[:180]}"
        body_lines = [
            brief.get("headline", ""),
            f"Binding constraint: {brief.get('binding_constraint', 'n/a')}",
            f"New fatigue signals: {len(signals)} · Proposed actions: {len(actions)}",
            "Open Aether → Performance for the full brief and one-click actions.",
        ]
        db.add(Notification(client_id=client.id, type="AETHER_BRIEFING",
                            title=title[:240], message="\n".join(filter(None, body_lines))))
        run = AutomationRun(client_id=client.id, kind="morning_report", status="DONE", output={
            "headline": brief.get("headline"),
            "binding_constraint": brief.get("binding_constraint"),
            "fatigue_signals": len(signals),
            "proposed_actions": len(actions),
            "problems": problem_count,
        })
        db.add(run)
        db.commit()

        _email_briefing(db, client, brief, len(signals), len(actions))
        return {"client_id": client_id, "ok": True, "problems": problem_count}
    except Exception as exc:
        log.exception("morning briefing failed for %s", client_id)
        return {"client_id": client_id, "ok": False, "error": str(exc)}
    finally:
        db.close()


def _email_briefing(db, client, brief: dict, n_signals: int, n_actions: int) -> None:
    try:
        from app.services.email import send_email  # existing CRUX service
        user = client.user
        if not user or not user.email:
            return
        send_email(
            to=user.email,
            subject=f"Aether morning briefing — {client.company_name}",
            html=(f"<h2>{brief.get('headline', 'Your daily briefing')}</h2>"
                  f"<p><b>Binding constraint:</b> {brief.get('binding_constraint', 'n/a')}</p>"
                  f"<p>{n_signals} fatigue signals · {n_actions} proposed optimizations</p>"
                  f"<p>Open your dashboard for the full analysis and one-click actions.</p>"),
        )
    except Exception:
        log.debug("briefing email skipped", exc_info=True)


@celery_app.task(name="aether.fatigue_scan_all")
def fatigue_scan_all() -> dict[str, Any]:
    from app.models.aether import AutomationRun
    from app.modules.creative_optimizer import detect_fatigue
    db = _session()
    try:
        total = 0
        for client in _active_clients(db):
            try:
                signals = detect_fatigue(db, client)
                total += len(signals)
                if signals:
                    db.add(AutomationRun(client_id=client.id, kind="fatigue_scan", status="DONE",
                                         output={"new_signals": len(signals)}))
                    db.commit()
            except Exception:
                log.exception("fatigue scan failed for %s", client.id)
        return {"new_signals": total}
    finally:
        db.close()


@celery_app.task(name="aether.budget_review_all")
def budget_review_all() -> dict[str, Any]:
    from app.models.aether import AutomationRun
    from app.modules.budget_optimizer import run_budget_review
    db = _session()
    try:
        total = 0
        for client in _active_clients(db):
            try:
                actions = run_budget_review(db, client)
                total += len(actions)
                db.add(AutomationRun(client_id=client.id, kind="budget_review", status="DONE",
                                     output={"proposed_actions": len(actions)}))
                db.commit()
            except Exception:
                log.exception("budget review failed for %s", client.id)
        return {"proposed_actions": total}
    finally:
        db.close()


@celery_app.task(name="aether.retrain_models_all")
def retrain_models_all() -> dict[str, Any]:
    from app.ml.predictors import train_account_models
    from app.models.aether import AutomationRun
    db = _session()
    try:
        reports = {}
        for client in _active_clients(db):
            try:
                reports[client.id] = train_account_models(db, client.id)
            except Exception as exc:
                reports[client.id] = {"trained": False, "reason": str(exc)}
        db.add(AutomationRun(client_id=None, kind="model_retrain", status="DONE",
                             output={"reports": {k: v for k, v in list(reports.items())[:50]}}))
        db.commit()
        return {"accounts": len(reports)}
    finally:
        db.close()
