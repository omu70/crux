"""Module 10 — AI Research Engine.

Multi-source market research: Reddit, YouTube, Google, Quora, Amazon reviews,
Trustpilot, app reviews, blogs, forums, competitors. Public JSON endpoints are
used where they exist without keys (Reddit search, DuckDuckGo lite HTML);
everything else is synthesized by the Research agent from what was gathered.
Findings land in the RAG store (namespace "research") and as a ResearchJob row.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.agents.prompts import ROLE_PROMPTS
from app.ai.router import llm
from app.models.aether import ResearchJob
from app.models.models import Client
from app.modules.business_intel import business_context_snippet
from app.rag.ingest import ingest_text

log = logging.getLogger("aether.research")

SOURCES = ["reddit", "youtube", "google", "quora", "amazon", "trustpilot",
           "app_reviews", "blogs", "forums", "competitors"]

_UA = {"User-Agent": "Mozilla/5.0 (compatible; AetherAI/1.0)"}

SUMMARY_SHAPE = {
    "summary": "market research executive summary, 1 paragraph",
    "insights": [{"insight": "specific market insight", "evidence": "where it came from",
                  "marketing_use": "how to use it in ads/offers"}],
    "voice_of_customer": [{"phrase": "verbatim-style customer phrase", "emotion": "the emotion behind it",
                           "use_as": "hook|objection-handler|testimonial-angle"}],
    "hidden_motivations": ["non-obvious buying motivation discovered"],
    "content_gaps": ["question customers ask that nobody answers well"],
}


def _search_reddit(query: str, limit: int = 8) -> list[dict[str, Any]]:
    try:
        r = httpx.get("https://www.reddit.com/search.json",
                      params={"q": query, "limit": limit, "sort": "relevance", "t": "year"},
                      headers=_UA, timeout=20)
        r.raise_for_status()
        posts = r.json().get("data", {}).get("children", [])
        return [{
            "source": "reddit",
            "title": p["data"].get("title", ""),
            "text": (p["data"].get("selftext") or "")[:1200],
            "subreddit": p["data"].get("subreddit"),
            "score": p["data"].get("score"),
            "url": "https://reddit.com" + p["data"].get("permalink", ""),
        } for p in posts]
    except Exception as exc:
        log.warning("reddit search failed: %s", exc)
        return []


def _search_web(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """DuckDuckGo HTML (no key) as a generic google/blogs/forums proxy."""
    try:
        r = httpx.get("https://html.duckduckgo.com/html/", params={"q": query},
                      headers=_UA, timeout=20)
        r.raise_for_status()
        import re
        results = []
        for m in re.finditer(
                r'result__a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?result__snippet[^>]*>(.*?)</',
                r.text, re.DOTALL):
            url, title, snippet = m.groups()
            clean = lambda s: re.sub(r"<[^>]+>", "", s).strip()
            results.append({"source": "web", "url": url, "title": clean(title),
                            "text": clean(snippet)[:800]})
            if len(results) >= limit:
                break
        return results
    except Exception as exc:
        log.warning("web search failed: %s", exc)
        return []


def run_research(db: Session, client: Client, query: str,
                 sources: list[str] | None = None) -> ResearchJob:
    sources = [s for s in (sources or SOURCES) if s in SOURCES] or SOURCES
    job = ResearchJob(client_id=client.id, query=query[:500], sources=sources, status="RUNNING")
    db.add(job)
    db.commit()

    findings: dict[str, list[dict[str, Any]]] = {}
    try:
        if "reddit" in sources:
            findings["reddit"] = _search_reddit(query)
        web_targets = {
            "google": query,
            "youtube": f"site:youtube.com {query}",
            "quora": f"site:quora.com {query}",
            "amazon": f"site:amazon.com reviews {query}",
            "trustpilot": f"site:trustpilot.com {query}",
            "app_reviews": f"app review {query}",
            "blogs": f"{query} blog honest review",
            "forums": f"{query} forum discussion",
        }
        for src, q in web_targets.items():
            if src in sources:
                findings[src] = _search_web(q, limit=5)

        gathered = []
        for src, items in findings.items():
            for it in items:
                gathered.append(f"[{src}] {it.get('title', '')} — {it.get('text', '')}")
        gathered_text = "\n".join(gathered)[:14000] or "(no external results fetched — synthesize from market knowledge, marking everything as inference)"

        import json
        data = llm.complete_json(
            role="research", system=ROLE_PROMPTS["research"],
            user=(f"CLIENT:\n{business_context_snippet(db, client.id)}\n\n"
                  f"RESEARCH QUERY: {query}\nSOURCES SCRAPED: {sources}\n\n"
                  f"RAW FINDINGS:\n{gathered_text}\n\n"
                  "Mine this for marketing gold. Voice-of-customer must sound human, not corporate."),
            shape=SUMMARY_SHAPE, client_id=client.id, temperature=0.5,
        ) or {}

        job.results = {k: v[:8] for k, v in findings.items()}
        job.summary = data.get("summary")
        job.insights = data.get("insights")
        job.voice_of_customer = data.get("voice_of_customer")
        job.status = "DONE"
        job.finished_at = dt.datetime.now(dt.timezone.utc)
        db.commit()

        # persist to RAG for every downstream module
        try:
            ingest_text(
                db, client.id, f"Research: {query[:120]}",
                f"Summary: {job.summary}\nInsights: {json.dumps(job.insights)[:4000]}\n"
                f"Voice of customer: {json.dumps(job.voice_of_customer)[:4000]}\n"
                f"Hidden motivations: {data.get('hidden_motivations')}",
                namespace="research", source_type="manual",
            )
        except Exception:
            log.debug("research self-ingest skipped", exc_info=True)
    except Exception as exc:
        log.exception("research job failed")
        job.status = "FAILED"
        job.summary = f"Research failed: {exc}"
        db.commit()
    return job


def serialize_research(j: ResearchJob) -> dict:
    return {
        "id": j.id, "query": j.query, "sources": j.sources, "status": j.status,
        "results": j.results or {}, "summary": j.summary,
        "insights": j.insights or [], "voice_of_customer": j.voice_of_customer or [],
        "created_at": j.created_at.isoformat(),
        "finished_at": j.finished_at.isoformat() if j.finished_at else None,
    }
