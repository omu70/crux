"""Authentication routes: login, admin login, refresh, me, forgot-password."""
from __future__ import annotations

import datetime as dt

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token, create_refresh_token, decode_token, verify_password,
)
from app.models import User
from app.schemas import LoginRequest, RefreshRequest, TokenPair, UserOut
from app.services.email import send_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _authenticate(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is inactive")
    return user


def _issue(user_id: str, role: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id, role),
    )


def _record_login(db: Session, user: User, request: Request, action: str) -> None:
    """Best-effort last-login + audit write. Never lets a write failure break the
    actual login — the tokens are already safe to issue from the read above."""
    try:
        user.last_login_at = dt.datetime.now(dt.timezone.utc)
        ip = request.client.host if request.client else None
        log_action(db, user_id=user.id, action=action, entity="user", entity_id=user.id, ip=ip, commit=False)
        db.commit()
    except Exception:
        db.rollback()


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = _authenticate(db, body.username, body.password)
    uid, role = user.id, user.role
    _record_login(db, user, request, "login")
    return _issue(uid, role)


@router.post("/admin/login", response_model=TokenPair)
def admin_login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = _authenticate(db, body.username, body.password)
    if user.role != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not an admin account")
    uid, role = user.id, user.role
    _record_login(db, user, request, "admin_login")
    return _issue(uid, role)


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return _issue(user.id, user.role)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password")
def forgot_password(payload: dict, db: Session = Depends(get_db)):
    """Always returns ok (avoids account enumeration). Emails a reset link if
    the address exists and Resend is configured."""
    username = payload.get("username", "")
    user = db.query(User).filter(User.username == username).first()
    if user:
        send_email(user.email, "Reset your CRUX password",
                   "<p>A password reset was requested. Contact your DiziGroww account manager to complete the reset.</p>")
    return {"ok": True, "message": "If that account exists, reset instructions have been sent."}


@router.post("/bootstrap")
def bootstrap(db: Session = Depends(get_db)):
    """One-time seeding for a fresh deploy. Runs the seed ONLY when the database
    has no users; refuses (safely) once seeded. Reports the exact error if the
    seed fails, so an empty-database deploy can be diagnosed + fixed."""
    from app.core.database import init_db
    init_db()  # ensure the schema exists (safe no-op if already created)
    existing = db.query(User).count()
    if existing > 0:
        return {"seeded": False, "reason": "already_seeded", "users": existing}
    try:
        from app import seed
        seed.run()
    except Exception as exc:  # surface the real failure
        import traceback
        return {"seeded": False, "error": str(exc), "trace": traceback.format_exc()[-2000:]}
    return {"seeded": True, "users": db.query(User).count()}
