"""CRUX by DiziGroww — FastAPI application entrypoint."""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.core.rate_limit import RateLimitMiddleware
from app.routers import admin, aether, auth, clients, collab, dashboard, insights, marketing

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="CRUX by DiziGroww API",
    description="Where Growth Becomes Crystal Clear. — client-portal backend.",
    version="1.0.0",
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# ── Static (local file uploads fallback) ─────────────────────────────────────
_uploads = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(_uploads, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(marketing.router)
app.include_router(insights.router)
app.include_router(collab.router)
app.include_router(clients.router)
app.include_router(admin.router)
app.include_router(aether.router)


@app.on_event("startup")
def _startup() -> None:
    # Dev/test convenience: ensure tables exist. In production against Supabase,
    # apply prisma/migrations/0001_init/migration.sql instead.
    init_db()


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):  # pragma: no cover
    logging.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", tags=["health"])
def root():
    return {"name": "CRUX by DiziGroww API", "status": "ok", "docs": "/docs"}


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}
