"""Admin client-management routes."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.database import get_db
from app.core.deps import require_admin
from app.core.security import create_access_token, hash_password
from app.models import AccountManager, Client, Integration, MetricSnapshot, User
from app.schemas import (
    ClientCreate, ClientCredentials, ClientOut, ClientUpdate, GenericOK,
    IntegrationConnect, IntegrationOut,
)
from app.services.meta_import import import_meta_export, parse_table
from app.services.meta_sync import sync_meta

router = APIRouter(prefix="/api/admin/clients", tags=["admin:clients"])


def _get_client(db: Session, client_id: str) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")
    return client


@router.get("", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(Client).order_by(Client.created_at.desc()).all()


@router.post("", response_model=ClientOut, status_code=201)
def create_client(body: ClientCreate, request: Request,
                  db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.query(User).filter((User.username == body.username) | (User.email == body.email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already exists")

    user = User(
        email=body.email, username=body.username,
        password_hash=hash_password(body.password), role="CLIENT", is_active=True,
    )
    db.add(user)
    db.flush()

    client = Client(
        user_id=user.id, company_name=body.company_name, contact_name=body.contact_name,
        plan=body.plan, monthly_budget=body.monthly_budget,
        monthly_target_revenue=body.monthly_target_revenue,
        monthly_target_roas=body.monthly_target_roas,
        monthly_target_leads=body.monthly_target_leads,
        account_manager_id=body.account_manager_id, currency=body.currency, timezone=body.timezone,
    )
    db.add(client)
    db.flush()
    log_action(db, user_id=admin.id, action="create_client", entity="client", entity_id=client.id,
               ip=request.client.host if request.client else None, meta={"company": body.company_name}, commit=False)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: str, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return _get_client(db, client_id)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: str, body: ClientUpdate,
                  db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    client = _get_client(db, client_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    log_action(db, user_id=admin.id, action="update_client", entity="client", entity_id=client.id, commit=False)
    db.commit()
    db.refresh(client)
    return client


@router.patch("/{client_id}/targets", response_model=ClientOut)
def assign_targets(client_id: str, body: ClientUpdate,
                   db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Assign monthly targets/budget (subset of update, kept as a clear endpoint)."""
    return update_client(client_id, body, db, admin)


@router.patch("/{client_id}/credentials", response_model=GenericOK)
def assign_credentials(client_id: str, body: ClientCredentials,
                       db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    client = _get_client(db, client_id)
    user = db.get(User, client.user_id)
    if body.username:
        if db.query(User).filter(User.username == body.username, User.id != user.id).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
        user.username = body.username
    if body.password:
        user.password_hash = hash_password(body.password)
    log_action(db, user_id=admin.id, action="assign_credentials", entity="client", entity_id=client.id, commit=False)
    db.commit()
    return GenericOK(id=client.id)


@router.post("/{client_id}/suspend", response_model=ClientOut)
def suspend_client(client_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    client = _get_client(db, client_id)
    client.status = "SUSPENDED"
    log_action(db, user_id=admin.id, action="suspend_client", entity="client", entity_id=client.id, commit=False)
    db.commit()
    db.refresh(client)
    return client


@router.post("/{client_id}/activate", response_model=ClientOut)
def activate_client(client_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    client = _get_client(db, client_id)
    client.status = "ACTIVE"
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", response_model=GenericOK)
def delete_client(client_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    client = _get_client(db, client_id)
    user = db.get(User, client.user_id)
    db.delete(client)
    if user:
        db.delete(user)
    log_action(db, user_id=admin.id, action="delete_client", entity="client", entity_id=client_id, commit=False)
    db.commit()
    return GenericOK(id=client_id)


# ── Integrations ─────────────────────────────────────────────────────────────
@router.get("/{client_id}/integrations", response_model=list[IntegrationOut])
def list_integrations(client_id: str, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(Integration).filter(Integration.client_id == client_id).all()


@router.post("/{client_id}/integrations", response_model=IntegrationOut)
def connect_integration(client_id: str, body: IntegrationConnect,
                        db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    _get_client(db, client_id)
    integ = db.query(Integration).filter(
        Integration.client_id == client_id, Integration.type == body.type).first()
    if integ is None:
        integ = Integration(client_id=client_id, type=body.type)
        db.add(integ)
    integ.status = body.status
    integ.external_id = body.external_id
    integ.account_name = body.account_name
    integ.config = body.config
    integ.last_synced_at = dt.datetime.now(dt.timezone.utc)
    log_action(db, user_id=admin.id, action="connect_integration", entity="integration",
               entity_id=client_id, meta={"type": body.type}, commit=False)
    db.commit()
    db.refresh(integ)
    return integ


# ── Manual metric entry (admin supplies each client's data) ──────────────────
@router.post("/{client_id}/metrics", response_model=GenericOK)
def upsert_metric(client_id: str, body: dict,
                  db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Upsert a single day's metric snapshot. Body keys mirror MetricSnapshot.

    Example: {"date": "2026-07-01", "revenue": 5230, "orders": 42, "ad_spend": 1200, ...}
    """
    _get_client(db, client_id)
    date_str = body.get("date")
    if not date_str:
        raise HTTPException(422, "date is required (YYYY-MM-DD)")
    date = dt.date.fromisoformat(date_str)
    row = db.query(MetricSnapshot).filter(
        MetricSnapshot.client_id == client_id, MetricSnapshot.date == date).first()
    if row is None:
        row = MetricSnapshot(client_id=client_id, date=date)
        db.add(row)
    for k, v in body.items():
        if k != "date" and hasattr(row, k):
            setattr(row, k, v)
    log_action(db, user_id=admin.id, action="upsert_metric", entity="metric", entity_id=client_id, commit=False)
    db.commit()
    return GenericOK(id=row.id)


# ── Switch into client dashboard ─────────────────────────────────────────────
@router.post("/{client_id}/switch")
def switch_into_client(client_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Return a short-lived CLIENT access token so an admin can view the client
    dashboard exactly as the client sees it."""
    client = _get_client(db, client_id)
    token = create_access_token(client.user_id, "CLIENT")
    log_action(db, user_id=admin.id, action="switch_into_client", entity="client", entity_id=client_id)
    return {"access_token": token, "token_type": "bearer", "client_id": client_id}


# ── Meta Ads: connect + one-click sync ───────────────────────────────────────
@router.post("/{client_id}/integrations/meta/connect", response_model=IntegrationOut)
def connect_meta(client_id: str, body: dict,
                 db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Store the client's Meta Ad Account ID (and optional per-client token).

    Body: {"ad_account_id": "act_123... or 123...", "access_token": "optional"}.
    If access_token is omitted, the server-wide META_ACCESS_TOKEN env var is used.
    """
    _get_client(db, client_id)
    ad_account = (body.get("ad_account_id") or "").strip()
    if not ad_account:
        raise HTTPException(422, "ad_account_id is required")
    integ = db.query(Integration).filter(
        Integration.client_id == client_id, Integration.type == "META_ADS").first()
    if integ is None:
        integ = Integration(client_id=client_id, type="META_ADS")
        db.add(integ)
    config = {"ad_account_id": ad_account}
    if body.get("access_token"):
        config["access_token"] = body["access_token"]
    integ.config = config
    integ.account_name = ad_account
    integ.status = "CONNECTED"
    log_action(db, user_id=admin.id, action="connect_meta", entity="integration", entity_id=client_id, commit=False)
    db.commit()
    db.refresh(integ)
    return integ


@router.post("/{client_id}/metrics/import")
async def import_metrics(client_id: str, file: UploadFile = File(...),
                         db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Import a Meta Ads Manager CSV/Excel export → daily metrics + campaigns."""
    client = _get_client(db, client_id)
    content = await file.read()
    try:
        rows = parse_table(file.filename or "export.csv", content)
        result = import_meta_export(db, client, rows)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(400, f"Could not read file: {exc}")
    log_action(db, user_id=admin.id, action="import_meta_export", entity="client", entity_id=client_id)
    return {"ok": True, **result}


@router.post("/{client_id}/integrations/meta/sync")
def meta_sync(client_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Pull the latest Meta campaigns + daily metrics into the client's dashboard."""
    client = _get_client(db, client_id)
    try:
        result = sync_meta(db, client)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:  # network / Meta API errors
        raise HTTPException(502, f"Meta API error: {exc}")
    log_action(db, user_id=admin.id, action="sync_meta", entity="client", entity_id=client_id)
    return {"ok": True, **result}
