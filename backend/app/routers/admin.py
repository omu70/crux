"""Admin operations: overview, audit logs, account managers, announcements,
notifications, integrations/API status, and content management (documents,
reports, tasks, goals, meeting notes, alerts)."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.audit import log_action
from app.core.database import get_db
from app.core.deps import require_admin
from app.models import (
    AccountManager, Alert, Announcement, AuditLog, Client, Document, Goal,
    MeetingNote, MetricSnapshot, Notification, Report, Task, User,
)
from app.schemas import (
    AnnouncementCreate, GenericOK, GoalCreate, MeetingNoteCreate, NotificationCreate,
)
from app.services.storage import save_file

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    clients = db.query(Client).all()
    total_revenue = db.query(func.coalesce(func.sum(MetricSnapshot.revenue), 0)).scalar() or 0
    total_spend = db.query(func.coalesce(func.sum(MetricSnapshot.ad_spend), 0)).scalar() or 0
    recent = (db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all())
    return {
        "clients": {
            "total": len(clients),
            "active": sum(1 for c in clients if c.status == "ACTIVE"),
            "suspended": sum(1 for c in clients if c.status == "SUSPENDED"),
        },
        "tracked_revenue": round(float(total_revenue), 2),
        "tracked_ad_spend": round(float(total_spend), 2),
        "recent_activity": [{"action": a.action, "entity": a.entity, "entity_id": a.entity_id,
                             "created_at": a.created_at.isoformat()} for a in recent],
    }


@router.get("/audit-logs")
def audit_logs(limit: int = 100, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [{"id": a.id, "user_id": a.user_id, "action": a.action, "entity": a.entity,
             "entity_id": a.entity_id, "ip": a.ip, "created_at": a.created_at.isoformat()} for a in rows]


@router.get("/api-status")
def api_status(_: User = Depends(require_admin)):
    """Report which external services have credentials configured."""
    def st(flag: bool) -> str:
        return "connected" if flag else "not_configured"
    return {
        "database": "connected",
        "supabase_storage": st(bool(settings.SUPABASE_SERVICE_ROLE_KEY)),
        "gemini_ai": st(bool(settings.GEMINI_API_KEY)),
        "resend_email": st(bool(settings.RESEND_API_KEY)),
        "meta_ads": st(bool(settings.META_ACCESS_TOKEN)),
        "shopify": st(bool(settings.SHOPIFY_ADMIN_TOKEN)),
        "woocommerce": st(bool(settings.WOOCOMMERCE_KEY)),
        "ga4": st(bool(settings.GA4_PROPERTY_ID)),
        "search_console": st(bool(settings.SEARCH_CONSOLE_SITE_URL)),
    }


# ── Account managers ─────────────────────────────────────────────────────────
@router.get("/account-managers")
def list_managers(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [{"id": m.id, "name": m.name, "email": m.email, "title": m.title,
             "avatar_url": m.avatar_url} for m in db.query(AccountManager).all()]


@router.post("/account-managers", response_model=GenericOK)
def create_manager(body: dict, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    m = AccountManager(name=body["name"], email=body["email"],
                       title=body.get("title", "Account Manager"), avatar_url=body.get("avatar_url"))
    db.add(m)
    db.commit()
    return GenericOK(id=m.id)


# ── Announcements & notifications ────────────────────────────────────────────
@router.get("/announcements")
def list_announcements(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return [{"id": a.id, "title": a.title, "message": a.message,
             "created_at": a.created_at.isoformat()} for a in rows]


@router.post("/announcements", response_model=GenericOK)
def push_announcement(body: AnnouncementCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    a = Announcement(title=body.title, message=body.message, created_by=admin.username)
    db.add(a)
    # Fan out as a notification to every client too.
    for c in db.query(Client).all():
        db.add(Notification(client_id=c.id, type="GENERAL", title=body.title, message=body.message))
    db.commit()
    return GenericOK(id=a.id)


@router.post("/notifications", response_model=GenericOK)
def send_notification(body: NotificationCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    targets = ([db.get(Client, body.client_id)] if body.client_id else db.query(Client).all())
    for c in targets:
        if c:
            db.add(Notification(client_id=c.id, type=body.type, title=body.title, message=body.message))
    db.commit()
    return GenericOK()


# ── Content management (per client) ──────────────────────────────────────────
@router.post("/clients/{client_id}/documents", response_model=GenericOK)
async def upload_document(
    client_id: str,
    category: str = Form("OTHER"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if db.get(Client, client_id) is None:
        raise HTTPException(404, "Client not found")
    content = await file.read()
    url = save_file(file.filename or "file", content, file.content_type or "application/octet-stream")
    doc = Document(client_id=client_id, name=file.filename or "file", category=category,
                   file_type=(file.content_type or "").split("/")[-1] or "bin",
                   file_url=url, size_bytes=len(content), uploaded_by=admin.username)
    db.add(doc)
    log_action(db, user_id=admin.id, action="upload_document", entity="document", entity_id=client_id, commit=False)
    db.commit()
    return GenericOK(id=doc.id)


@router.post("/clients/{client_id}/reports", response_model=GenericOK)
def create_report(client_id: str, body: dict, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.get(Client, client_id) is None:
        raise HTTPException(404, "Client not found")
    r = Report(client_id=client_id, title=body["title"], month=body.get("month", ""),
               summary=body.get("summary", ""), wins=body.get("wins"), losses=body.get("losses"),
               kpis=body.get("kpis"), suggestions=body.get("suggestions"),
               strategy=body.get("strategy"), file_url=body.get("file_url"), created_by=admin.username)
    db.add(r)
    db.commit()
    return GenericOK(id=r.id)


@router.post("/clients/{client_id}/tasks", response_model=GenericOK)
def create_task_admin(client_id: str, body: dict, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    t = Task(client_id=client_id, title=body["title"], description=body.get("description"),
             status=body.get("status", "PENDING"), priority=body.get("priority", "MEDIUM"),
             responsible=body.get("responsible"), expected_result=body.get("expected_result"),
             timeframe=body.get("timeframe", "week"))
    db.add(t)
    db.commit()
    return GenericOK(id=t.id)


@router.post("/clients/{client_id}/goals", response_model=GenericOK)
def create_goal_admin(client_id: str, body: GoalCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    g = Goal(client_id=client_id, **body.model_dump())
    db.add(g)
    db.commit()
    return GenericOK(id=g.id)


@router.post("/clients/{client_id}/meeting-notes", response_model=GenericOK)
def create_meeting_note(client_id: str, body: MeetingNoteCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    m = MeetingNote(client_id=client_id, title=body.title, notes=body.notes,
                    action_items=body.action_items, recording_url=body.recording_url,
                    meeting_date=body.meeting_date)
    db.add(m)
    db.commit()
    return GenericOK(id=m.id)


@router.post("/clients/{client_id}/alerts", response_model=GenericOK)
def create_alert(client_id: str, body: dict, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    a = Alert(client_id=client_id, type=body["type"], severity=body.get("severity", "WARNING"),
              title=body["title"], message=body["message"])
    db.add(a)
    db.commit()
    return GenericOK(id=a.id)
