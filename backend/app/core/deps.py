"""Shared FastAPI dependencies: authentication and role-based access."""
from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import Client, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(creds.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
        user_id = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


def get_current_client(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Client:
    """Resolve the Client record for the logged-in client user."""
    if user.role != "CLIENT":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client access required")
    client = db.query(Client).filter(Client.user_id == user.id).first()
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client profile not found")
    if client.status == "SUSPENDED":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account suspended. Contact your account manager.")
    return client
