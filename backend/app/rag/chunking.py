"""Text chunking for the RAG store — paragraph-aware sliding windows."""
from __future__ import annotations

import re

CHUNK_TOKENS = 400          # target chunk size (approx tokens)
OVERLAP_TOKENS = 60         # overlap between consecutive chunks
CHARS_PER_TOKEN = 4         # cheap approximation, good enough for sizing


def approx_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def chunk_text(text: str) -> list[str]:
    """Split into ~CHUNK_TOKENS chunks on paragraph, then sentence boundaries."""
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not text:
        return []
    max_chars = CHUNK_TOKENS * CHARS_PER_TOKEN
    overlap_chars = OVERLAP_TOKENS * CHARS_PER_TOKEN

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        candidate = f"{buf}\n\n{para}".strip() if buf else para
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        # paragraph itself may exceed the window → sentence-split it
        if len(para) > max_chars:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            buf = ""
            for s in sentences:
                cand = f"{buf} {s}".strip() if buf else s
                if len(cand) <= max_chars:
                    buf = cand
                else:
                    if buf:
                        chunks.append(buf)
                    buf = s[:max_chars]
        else:
            buf = para
    if buf:
        chunks.append(buf)

    # add trailing overlap from previous chunk for retrieval continuity
    with_overlap: list[str] = []
    for i, c in enumerate(chunks):
        if i and overlap_chars:
            tail = chunks[i - 1][-overlap_chars:]
            c = tail + "\n" + c
        with_overlap.append(c)
    return with_overlap
