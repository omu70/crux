"""Celery application + beat schedule for Aether automations.

With CELERY_BROKER_URL/REDIS_URL set, run:
    celery -A app.worker worker --loglevel=info
    celery -A app.worker beat   --loglevel=info

Without a broker, `task_always_eager` makes every .delay() run in-process, so
dev/tests need no Redis.
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "aether",
    broker=settings.celery_broker or "memory://",
    backend=settings.celery_backend or "cache+memory://",
    include=["app.tasks.automations"],
)

celery_app.conf.update(
    task_always_eager=not bool(settings.celery_broker),
    task_eager_propagates=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        # Every morning: report + problems + action plan + notify (per client).
        "morning-briefing": {
            "task": "aether.morning_briefing_all",
            "schedule": crontab(hour=8, minute=0),
        },
        # Fatigue scan twice a day.
        "fatigue-scan": {
            "task": "aether.fatigue_scan_all",
            "schedule": crontab(hour="9,17", minute=30),
        },
        # Budget review daily before the US morning.
        "budget-review": {
            "task": "aether.budget_review_all",
            "schedule": crontab(hour=11, minute=0),
        },
        # Retrain per-account prediction models weekly.
        "retrain-models": {
            "task": "aether.retrain_models_all",
            "schedule": crontab(hour=3, minute=0, day_of_week="mon"),
        },
    },
)
