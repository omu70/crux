"""Knowledge ingestion — URLs, raw text, PDFs, CSVs → documents + embeddings."""
from __future__ import annotations

import logging
import re

import httpx
from sqlalchemy.orm import Session

from app.models.aether import KnowledgeDocument
from app.rag.chunking import chunk_text
from app.rag.store import store_chunks

log = logging.getLogger("aether.ingest")

_UA = {"User-Agent": "Mozilla/5.0 (compatible; AetherAI/1.0; +https://aether.ai/bot)"}


def html_to_text(html: str) -> str:
    """Dependency-free HTML → text (good enough for marketing pages)."""
    html = re.sub(r"(?is)<(script|style|noscript|svg|head)[^>]*>.*?</\1>", " ", html)
    # keep some structure signals
    html = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|section|article)>", "\n", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'")
                .replace("&quot;", '"'))
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_page_text(url: str, timeout: int = 25) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    r = httpx.get(url, headers=_UA, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    ctype = r.headers.get("content-type", "")
    if "html" in ctype or ctype == "":
        return html_to_text(r.text)
    return r.text[:200_000]


def ingest_text(db: Session, client_id: str, title: str, content: str, *,
                namespace: str = "general", source_type: str = "text",
                source_url: str | None = None, meta: dict | None = None) -> KnowledgeDocument:
    doc = KnowledgeDocument(
        client_id=client_id, namespace=namespace, title=title[:300],
        source_type=source_type, source_url=source_url,
        content=content[:500_000], meta=meta,
    )
    db.add(doc)
    db.flush()
    store_chunks(db, doc, chunk_text(doc.content))
    return doc


def ingest_url(db: Session, client_id: str, url: str, *,
               namespace: str = "business", title: str | None = None) -> KnowledgeDocument:
    text = fetch_page_text(url)
    return ingest_text(
        db, client_id, title or url, text,
        namespace=namespace, source_type="url", source_url=url,
    )


def ingest_pdf_bytes(db: Session, client_id: str, filename: str, data: bytes, *,
                     namespace: str = "brand") -> KnowledgeDocument:
    """PDF text extraction via pypdf when installed; degrades to a stub doc."""
    text = ""
    try:
        import io
        from pypdf import PdfReader  # optional dependency
        reader = PdfReader(io.BytesIO(data))
        text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:
        log.warning("PDF extraction unavailable/failed (%s); storing metadata only", exc)
        text = f"(PDF uploaded: {filename}; install pypdf for text extraction)"
    return ingest_text(db, client_id, filename, text, namespace=namespace, source_type="pdf")


def ingest_csv_text(db: Session, client_id: str, filename: str, csv_text: str, *,
                    namespace: str = "business") -> KnowledgeDocument:
    """CSV → readable row summaries (first 300 rows) for retrieval."""
    import csv
    import io
    rows = list(csv.reader(io.StringIO(csv_text)))
    if not rows:
        return ingest_text(db, client_id, filename, "(empty csv)", namespace=namespace, source_type="csv")
    header, body = rows[0], rows[1:301]
    lines = [", ".join(f"{h}: {v}" for h, v in zip(header, r)) for r in body]
    content = f"CSV {filename} — columns: {', '.join(header)}\n" + "\n".join(lines)
    return ingest_text(db, client_id, filename, content, namespace=namespace, source_type="csv")
