"""SQLAlchemy engine, session factory and declarative base.

The backend runs on either PostgreSQL (Supabase / Docker) or SQLite (zero-setup
local dev + tests). Column types are chosen to be portable across both.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.sqlalchemy_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables that don't yet exist (safe to call repeatedly).

    In production against Supabase, prefer applying the Prisma migration
    (`prisma/migrations/0001_init/migration.sql`) which creates native enum
    types and UUID defaults. `create_all` is the zero-config dev/test path.
    """
    from app import models  # noqa: F401  (register models on Base.metadata)

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover - keeps the service booting
        import logging
        logging.getLogger("crux").error("Database init failed: %s", exc)
