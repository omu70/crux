"""Audit-log helper."""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    *,
    user_id: Optional[str],
    action: str,
    entity: Optional[str] = None,
    entity_id: Optional[str] = None,
    ip: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
    commit: bool = True,
) -> None:
    db.add(AuditLog(user_id=user_id, action=action, entity=entity,
                    entity_id=entity_id, ip=ip, meta=meta))
    if commit:
        db.commit()
