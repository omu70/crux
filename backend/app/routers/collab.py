"""Client collaboration surface: tasks, goals, meetings, notifications,
documents, tickets and live chat."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_client
from app.models import (
    ChatMessage, Client, Document, Goal, MeetingNote, Notification, Task,
    Ticket, TicketMessage,
)
from app.schemas import (
    ChatSend, GenericOK, TaskCreate, TaskUpdate, TicketCreate, TicketReply,
)

router = APIRouter(prefix="/api", tags=["collaboration"])


# ── Tasks ────────────────────────────────────────────────────────────────────
@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = db.query(Task).filter(Task.client_id == client.id).order_by(Task.created_at.desc()).all()
    def dump(t: Task):
        return {"id": t.id, "title": t.title, "description": t.description, "status": t.status,
                "priority": t.priority, "timeframe": t.timeframe, "responsible": t.responsible,
                "expected_result": t.expected_result,
                "due_date": t.due_date.isoformat() if t.due_date else None}
    data = [dump(t) for t in rows]
    return {
        "tasks": data,
        "buckets": {
            "completed": [t for t in data if t["status"] == "COMPLETED"],
            "in_progress": [t for t in data if t["status"] == "IN_PROGRESS"],
            "pending": [t for t in data if t["status"] == "PENDING"],
        },
    }


@router.post("/tasks", response_model=GenericOK)
def create_task(body: TaskCreate, db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    t = Task(client_id=client.id, **body.model_dump())
    db.add(t)
    db.commit()
    return GenericOK(id=t.id)


@router.patch("/tasks/{task_id}", response_model=GenericOK)
def update_task(task_id: str, body: TaskUpdate, db: Session = Depends(get_db),
                client: Client = Depends(get_current_client)):
    t = db.get(Task, task_id)
    if t is None or t.client_id != client.id:
        raise HTTPException(404, "Task not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    return GenericOK(id=t.id)


# ── Goals ────────────────────────────────────────────────────────────────────
@router.get("/goals")
def list_goals(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = db.query(Goal).filter(Goal.client_id == client.id).all()
    return [{"id": g.id, "type": g.type, "label": g.label, "target": g.target,
             "current": g.current, "unit": g.unit, "period": g.period,
             "progress": round(min(g.current / g.target * 100, 100), 1) if g.target else 0}
            for g in rows]


# ── Meeting notes ────────────────────────────────────────────────────────────
@router.get("/meeting-notes")
def list_meeting_notes(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(MeetingNote).filter(MeetingNote.client_id == client.id)
            .order_by(MeetingNote.meeting_date.desc()).all())
    return [{"id": m.id, "title": m.title, "notes": m.notes,
             "action_items": m.action_items or [], "recording_url": m.recording_url,
             "meeting_date": m.meeting_date.isoformat()} for m in rows]


# ── Notifications ────────────────────────────────────────────────────────────
@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(Notification).filter(Notification.client_id == client.id)
            .order_by(Notification.created_at.desc()).limit(50).all())
    return {
        "unread": sum(1 for n in rows if not n.read),
        "items": [{"id": n.id, "type": n.type, "title": n.title, "message": n.message,
                   "read": n.read, "created_at": n.created_at.isoformat()} for n in rows],
    }


@router.post("/notifications/{notification_id}/read", response_model=GenericOK)
def mark_read(notification_id: str, db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    n = db.get(Notification, notification_id)
    if n and n.client_id == client.id:
        n.read = True
        db.commit()
    return GenericOK(id=notification_id)


@router.post("/notifications/read-all", response_model=GenericOK)
def mark_all_read(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    db.query(Notification).filter(Notification.client_id == client.id, Notification.read == False).update(  # noqa: E712
        {"read": True})
    db.commit()
    return GenericOK()


# ── Documents ────────────────────────────────────────────────────────────────
@router.get("/documents")
def list_documents(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(Document).filter(Document.client_id == client.id)
            .order_by(Document.created_at.desc()).all())
    return [{"id": d.id, "name": d.name, "category": d.category, "file_type": d.file_type,
             "file_url": d.file_url, "size_bytes": d.size_bytes,
             "created_at": d.created_at.isoformat()} for d in rows]


# ── Tickets ──────────────────────────────────────────────────────────────────
@router.get("/tickets")
def list_tickets(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(Ticket).filter(Ticket.client_id == client.id)
            .order_by(Ticket.updated_at.desc()).all())
    return [{"id": t.id, "subject": t.subject, "description": t.description,
             "priority": t.priority, "status": t.status,
             "created_at": t.created_at.isoformat()} for t in rows]


@router.post("/tickets", response_model=GenericOK)
def create_ticket(body: TicketCreate, db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    t = Ticket(client_id=client.id, subject=body.subject, description=body.description, priority=body.priority)
    db.add(t)
    db.flush()
    db.add(TicketMessage(ticket_id=t.id, sender_id=client.user_id, body=body.description))
    db.commit()
    return GenericOK(id=t.id)


@router.get("/tickets/{ticket_id}")
def ticket_detail(ticket_id: str, db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    t = db.get(Ticket, ticket_id)
    if t is None or t.client_id != client.id:
        raise HTTPException(404, "Ticket not found")
    msgs = (db.query(TicketMessage).filter(TicketMessage.ticket_id == t.id)
            .order_by(TicketMessage.created_at.asc()).all())
    return {"id": t.id, "subject": t.subject, "status": t.status, "priority": t.priority,
            "messages": [{"id": m.id, "sender_id": m.sender_id, "body": m.body,
                          "created_at": m.created_at.isoformat()} for m in msgs]}


@router.post("/tickets/{ticket_id}/reply", response_model=GenericOK)
def reply_ticket(ticket_id: str, body: TicketReply, db: Session = Depends(get_db),
                 client: Client = Depends(get_current_client)):
    t = db.get(Ticket, ticket_id)
    if t is None or t.client_id != client.id:
        raise HTTPException(404, "Ticket not found")
    db.add(TicketMessage(ticket_id=t.id, sender_id=client.user_id, body=body.body))
    t.status = "IN_PROGRESS"
    db.commit()
    return GenericOK(id=t.id)


# ── Live chat ────────────────────────────────────────────────────────────────
@router.get("/chat")
def get_chat(db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    rows = (db.query(ChatMessage).filter(ChatMessage.client_id == client.id)
            .order_by(ChatMessage.created_at.asc()).limit(200).all())
    return [{"id": m.id, "sender_role": m.sender_role, "body": m.body,
             "created_at": m.created_at.isoformat()} for m in rows]


@router.post("/chat", response_model=GenericOK)
def send_chat(body: ChatSend, db: Session = Depends(get_db), client: Client = Depends(get_current_client)):
    m = ChatMessage(client_id=client.id, sender_id=client.user_id, sender_role="CLIENT", body=body.body)
    db.add(m)
    db.commit()
    return GenericOK(id=m.id)
