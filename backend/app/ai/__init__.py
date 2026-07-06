"""Aether AI core — multi-provider LLM router, embeddings, vision.

Public surface:
    from app.ai import llm, embed_texts, analyze_image_scores
"""
from app.ai.router import llm, LLMResult  # noqa: F401
from app.ai.embeddings import embed_texts, embed_query  # noqa: F401
from app.ai.vision import analyze_image_scores  # noqa: F401
