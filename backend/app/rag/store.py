"""Vector store over Postgres/pgvector with SQLite fallback.

On Postgres the migration adds `embedding_vec vector(N)`; writes keep it in
sync and reads use HNSW cosine search. On SQLite (dev/tests) vectors live in
the portable JSON column and similarity is computed in-process — identical
API, zero setup.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.ai.embeddings import cosine, embed_query, embed_texts
from app.core.config import settings
from app.models.aether import EmbeddingChunk, KnowledgeDocument

log = logging.getLogger("aether.rag")


def _pgvector_available(db: Session) -> bool:
    if settings.is_sqlite:
        return False
    try:
        db.execute(sql_text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).fetchone()
        return True
    except Exception:
        db.rollback()
        return False


def store_chunks(db: Session, document: KnowledgeDocument, chunks: list[str]) -> int:
    """Embed and persist chunks for a document. Returns count stored."""
    if not chunks:
        return 0
    vectors = embed_texts(chunks, client_id=document.client_id)
    rows: list[EmbeddingChunk] = []
    for i, (content, vec) in enumerate(zip(chunks, vectors)):
        rows.append(EmbeddingChunk(
            document_id=document.id, client_id=document.client_id,
            namespace=document.namespace, chunk_index=i, content=content,
            token_count=len(content) // 4, embedding=vec,
        ))
    db.add_all(rows)
    db.flush()

    if _pgvector_available(db):
        try:
            for row, vec in zip(rows, vectors):
                db.execute(
                    sql_text("UPDATE embedding_chunks SET embedding_vec = (:v)::vector WHERE id = :id"),
                    {"v": str(vec), "id": row.id},
                )
        except Exception as exc:  # keep JSON copy as source of truth
            db.rollback()
            log.warning("pgvector sync failed (JSON fallback still valid): %s", exc)
    db.commit()
    return len(rows)


def semantic_search(db: Session, client_id: str, query: str, *,
                    namespace: str | None = None, k: int = 8) -> list[dict[str, Any]]:
    """Return top-k chunks: [{content, score, document_id, namespace, title}]."""
    qvec = embed_query(query, client_id)

    if _pgvector_available(db):
        try:
            ns_clause = "AND c.namespace = :ns" if namespace else ""
            rows = db.execute(sql_text(f"""
                SELECT c.content, c.document_id, c.namespace, d.title,
                       1 - (c.embedding_vec <=> (:q)::vector) AS score
                FROM embedding_chunks c
                JOIN knowledge_documents d ON d.id = c.document_id
                WHERE c.client_id = :cid AND c.embedding_vec IS NOT NULL {ns_clause}
                ORDER BY c.embedding_vec <=> (:q)::vector
                LIMIT :k
            """), {"q": str(qvec), "cid": client_id, "k": k,
                   **({"ns": namespace} if namespace else {})}).fetchall()
            if rows:
                return [{"content": r[0], "document_id": r[1], "namespace": r[2],
                         "title": r[3], "score": round(float(r[4]), 4)} for r in rows]
        except Exception as exc:
            db.rollback()
            log.warning("pgvector search failed, using in-process cosine: %s", exc)

    # Portable path: cosine over JSON embeddings.
    q = db.query(EmbeddingChunk, KnowledgeDocument.title).join(
        KnowledgeDocument, KnowledgeDocument.id == EmbeddingChunk.document_id
    ).filter(EmbeddingChunk.client_id == client_id)
    if namespace:
        q = q.filter(EmbeddingChunk.namespace == namespace)
    scored = []
    for chunk, title in q.limit(5000).all():
        if not chunk.embedding:
            continue
        scored.append((cosine(qvec, chunk.embedding), chunk, title))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [{"content": c.content, "document_id": c.document_id, "namespace": c.namespace,
             "title": title, "score": round(s, 4)} for s, c, title in scored[:k]]


def build_context(db: Session, client_id: str, query: str, *,
                  namespaces: list[str] | None = None, k: int = 6,
                  max_chars: int = 8000) -> str:
    """Assemble a retrieval context block for agent prompts."""
    hits: list[dict[str, Any]] = []
    if namespaces:
        per_ns = max(2, k // len(namespaces))
        for ns in namespaces:
            hits.extend(semantic_search(db, client_id, query, namespace=ns, k=per_ns))
    else:
        hits = semantic_search(db, client_id, query, k=k)
    hits.sort(key=lambda h: h["score"], reverse=True)

    out, used = [], 0
    for h in hits:
        block = f"[{h['namespace']} · {h['title']} · relevance {h['score']}]\n{h['content']}"
        if used + len(block) > max_chars:
            break
        out.append(block)
        used += len(block)
    return "\n\n---\n\n".join(out) if out else "(no stored knowledge yet)"
