"""File storage abstraction.

If SUPABASE_SERVICE_ROLE_KEY is configured, files are uploaded to Supabase
Storage; otherwise they are written to a local `uploads/` directory served by
FastAPI's StaticFiles. Either way `save_file` returns a public URL.
"""
from __future__ import annotations

import os
import uuid

import httpx

from app.core.config import settings

LOCAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(LOCAL_DIR, exist_ok=True)


def save_file(filename: str, content: bytes, content_type: str = "application/octet-stream") -> str:
    safe = f"{uuid.uuid4().hex}_{filename}"

    if settings.SUPABASE_SERVICE_ROLE_KEY and settings.SUPABASE_URL:
        bucket = settings.SUPABASE_STORAGE_BUCKET
        url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{safe}"
        try:
            r = httpx.post(url, content=content, timeout=30, headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": content_type,
                "x-upsert": "true",
            })
            r.raise_for_status()
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{safe}"
        except Exception:  # pragma: no cover - network; fall back to local
            pass

    path = os.path.join(LOCAL_DIR, safe)
    with open(path, "wb") as fh:
        fh.write(content)
    return f"/uploads/{safe}"
