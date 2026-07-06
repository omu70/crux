"""LLM provider clients (OpenAI, Anthropic, Gemini) over plain httpx.

Deliberately SDK-free: one dependency (httpx, already used by CRUX), uniform
interface, easy mock. Each provider exposes:

    available() -> bool
    complete(messages, model, json_mode, max_tokens, temperature) -> ProviderResult
"""
from __future__ import annotations

import dataclasses
from typing import Any

import httpx

from app.core.config import settings

Message = dict[str, str]  # {"role": "system"|"user"|"assistant", "content": str}


@dataclasses.dataclass
class ProviderResult:
    text: str
    tokens_in: int
    tokens_out: int
    provider: str
    model: str


# Rough $/1M-token pricing for the cost ledger (update as prices change).
PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "gemini-2.0-flash": (0.10, 0.40),
    "text-embedding-3-large": (0.13, 0.0),
    "mock": (0.0, 0.0),
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = PRICES.get(model, (1.0, 3.0))
    return round((tokens_in * p_in + tokens_out * p_out) / 1_000_000, 6)


class OpenAIProvider:
    name = "openai"
    base = "https://api.openai.com/v1"

    def available(self) -> bool:
        return bool(settings.OPENAI_API_KEY) and not settings.AETHER_FORCE_MOCK

    def complete(self, messages: list[Message], model: str, json_mode: bool,
                 max_tokens: int, temperature: float) -> ProviderResult:
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        r = httpx.post(
            f"{self.base}/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json=body,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage", {})
        return ProviderResult(
            text=data["choices"][0]["message"]["content"] or "",
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            provider=self.name,
            model=model,
        )

    def embed(self, texts: list[str], model: str, dim: int) -> tuple[list[list[float]], int]:
        r = httpx.post(
            f"{self.base}/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model": model, "input": texts, "dimensions": dim},
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        r.raise_for_status()
        data = r.json()
        vecs = [row["embedding"] for row in sorted(data["data"], key=lambda x: x["index"])]
        return vecs, data.get("usage", {}).get("prompt_tokens", 0)


class AnthropicProvider:
    name = "anthropic"
    base = "https://api.anthropic.com/v1"

    def available(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY) and not settings.AETHER_FORCE_MOCK

    def complete(self, messages: list[Message], model: str, json_mode: bool,
                 max_tokens: int, temperature: float) -> ProviderResult:
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        convo = [m for m in messages if m["role"] != "system"]
        if json_mode:
            system += "\nRespond with a single valid JSON object and nothing else."
        r = httpx.post(
            f"{self.base}/messages",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "system": system or None,
                "messages": convo or [{"role": "user", "content": "Proceed."}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage", {})
        text = "".join(b.get("text", "") for b in data.get("content", []))
        return ProviderResult(
            text=text,
            tokens_in=usage.get("input_tokens", 0),
            tokens_out=usage.get("output_tokens", 0),
            provider=self.name,
            model=model,
        )


class GeminiProvider:
    name = "gemini"
    base = "https://generativelanguage.googleapis.com/v1beta"

    def available(self) -> bool:
        return bool(settings.GEMINI_API_KEY) and not settings.AETHER_FORCE_MOCK

    def complete(self, messages: list[Message], model: str, json_mode: bool,
                 max_tokens: int, temperature: float) -> ProviderResult:
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        contents = [
            {"role": "model" if m["role"] == "assistant" else "user",
             "parts": [{"text": m["content"]}]}
            for m in messages if m["role"] != "system"
        ]
        body: dict[str, Any] = {
            "contents": contents or [{"role": "user", "parts": [{"text": "Proceed."}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"
        r = httpx.post(
            f"{self.base}/models/{model}:generateContent",
            params={"key": settings.GEMINI_API_KEY},
            json=body,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        r.raise_for_status()
        data = r.json()
        usage = data.get("usageMetadata", {})
        candidates = data.get("candidates") or [{}]
        parts = candidates[0].get("content", {}).get("parts", [])
        return ProviderResult(
            text="".join(p.get("text", "") for p in parts),
            tokens_in=usage.get("promptTokenCount", 0),
            tokens_out=usage.get("candidatesTokenCount", 0),
            provider=self.name,
            model=model,
        )


OPENAI = OpenAIProvider()
ANTHROPIC = AnthropicProvider()
GEMINI = GeminiProvider()
