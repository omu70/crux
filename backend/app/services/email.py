"""Transactional email via Resend (optional).

If RESEND_API_KEY is not set, emails are logged and the function returns False
so callers can degrade gracefully.
"""
from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger("crux.email")


def send_email(to: str, subject: str, html: str) -> bool:
    if not settings.RESEND_API_KEY:
        logger.info("Email (noop, no RESEND_API_KEY) -> %s | %s", to, subject)
        return False
    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as exc:  # pragma: no cover - network
        logger.warning("Resend send failed: %s", exc)
        return False
