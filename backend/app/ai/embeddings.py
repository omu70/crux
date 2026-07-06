"""Embedding service — OpenAI text-embedding-3-large with deterministic mock
fallback. Vectors are normalized; dimension comes from settings.EMBEDDING_DIM.
"""
from __future__ import annotations

import logging

from app.ai import mock
from app.ai.providers import OPENAI, estimate_cost
from app.core.config import settings

log = logging.getLogger("aether.embeddings")

_BATCH = 64


def embed_texts(texts: list[str], client_id: str | None = None) -> list[list[float]]:
    """Embed a list of texts, preserving order."""
    if not texts:
        return []
    dim = settings.EMBEDDING_DIM
    if OPENAI.available():
        try:
            out: list[list[float]] = []
            total_tokens = 0
            for i in range(0, len(texts), _BATCH):
                vecs, tokens = OPENAI.embed(texts[i:i + _BATCH], settings.EMBEDDING_MODEL, dim)
                out.extend(vecs)
                total_tokens += tokens
            _ledger(client_id, total_tokens)
            return out
        except Exception as exc:
            log.warning("OpenAI embeddings failed, using mock: %s", exc)
    return [mock.mock_embedding(t, dim) for t in texts]


def embed_query(text: str, client_id: str | None = None) -> list[float]:
    return embed_texts([text], client_id)[0]


def cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = sum(x * x for x in a) ** 0.5
    db = sum(x * x for x in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def _ledger(client_id: str | None, tokens: int) -> None:
    try:
        import datetime as dt
        from app.core.database import SessionLocal
        from app.models.aether import UsageLedger
        db = SessionLocal()
        try:
            db.add(UsageLedger(
                client_id=client_id, date=dt.date.today(), provider="openai",
                model=settings.EMBEDDING_MODEL, tokens_in=tokens, tokens_out=0,
                cost_usd=estimate_cost(settings.EMBEDDING_MODEL, tokens, 0), kind="embedding",
            ))
            db.commit()
        finally:
            db.close()
    except Exception:  # pragma: no cover
        pass
