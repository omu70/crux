"""Unified LLM router.

Routes each agent role to a preferred provider/model, falls back across
providers on failure, and finally falls back to the deterministic mock so the
platform always answers. Records usage into the UsageLedger.

Usage:
    from app.ai import llm
    result = llm.complete_json(
        role="copy",
        system="You are a direct-response copywriter...",
        user="Write 5 hooks for ...",
        shape={"hooks": ["hook"]},
        client_id=client.id,
    )
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import logging
import re
import time
from typing import Any

from app.ai import mock
from app.ai.providers import (
    ANTHROPIC, GEMINI, OPENAI, Message, ProviderResult, estimate_cost,
)
from app.core.config import settings

log = logging.getLogger("aether.llm")


@dataclasses.dataclass
class LLMResult:
    text: str
    data: Any  # parsed JSON when json requested, else None
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: int


# Role → ordered (provider, model-settings-attr) preference. Strategy/decision
# work goes to the strongest models; bulk generation goes to fast models.
ROLE_ROUTES: dict[str, list[tuple[Any, str]]] = {
    "planner":      [(ANTHROPIC, "ANTHROPIC_MODEL"), (OPENAI, "LLM_DEFAULT_MODEL"), (GEMINI, "GEMINI_MODEL")],
    "research":     [(GEMINI, "GEMINI_MODEL"), (OPENAI, "LLM_FAST_MODEL"), (ANTHROPIC, "ANTHROPIC_MODEL")],
    "strategy":     [(ANTHROPIC, "ANTHROPIC_MODEL"), (OPENAI, "LLM_DEFAULT_MODEL"), (GEMINI, "GEMINI_MODEL")],
    "copy":         [(OPENAI, "LLM_DEFAULT_MODEL"), (ANTHROPIC, "ANTHROPIC_MODEL"), (GEMINI, "GEMINI_MODEL")],
    "creative":     [(OPENAI, "LLM_DEFAULT_MODEL"), (GEMINI, "GEMINI_MODEL"), (ANTHROPIC, "ANTHROPIC_MODEL")],
    "analytics":    [(OPENAI, "LLM_DEFAULT_MODEL"), (ANTHROPIC, "ANTHROPIC_MODEL"), (GEMINI, "GEMINI_MODEL")],
    "optimization": [(ANTHROPIC, "ANTHROPIC_MODEL"), (OPENAI, "LLM_DEFAULT_MODEL"), (GEMINI, "GEMINI_MODEL")],
    "memory":       [(OPENAI, "LLM_FAST_MODEL"), (GEMINI, "GEMINI_MODEL"), (ANTHROPIC, "ANTHROPIC_MODEL")],
    "decision":     [(ANTHROPIC, "ANTHROPIC_MODEL"), (OPENAI, "LLM_DEFAULT_MODEL"), (GEMINI, "GEMINI_MODEL")],
    "manager":      [(OPENAI, "LLM_FAST_MODEL"), (GEMINI, "GEMINI_MODEL"), (ANTHROPIC, "ANTHROPIC_MODEL")],
    "supervisor":   [(ANTHROPIC, "ANTHROPIC_MODEL"), (OPENAI, "LLM_DEFAULT_MODEL"), (GEMINI, "GEMINI_MODEL")],
    "default":      [(OPENAI, "LLM_DEFAULT_MODEL"), (ANTHROPIC, "ANTHROPIC_MODEL"), (GEMINI, "GEMINI_MODEL")],
}


def _extract_json(text: str) -> Any:
    """Parse JSON out of an LLM reply, tolerating code fences and prose."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # last resort: first {...} or [...] block
        for pattern in (r"\{.*\}", r"\[.*\]"):
            m = re.search(pattern, text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    continue
    raise ValueError("Model did not return valid JSON")


def _record_usage(client_id: str | None, res: ProviderResult, cost: float, kind: str = "llm") -> None:
    try:
        from app.core.database import SessionLocal
        from app.models.aether import UsageLedger
        db = SessionLocal()
        try:
            db.add(UsageLedger(
                client_id=client_id, date=dt.date.today(), provider=res.provider,
                model=res.model, tokens_in=res.tokens_in, tokens_out=res.tokens_out,
                cost_usd=cost, kind=kind,
            ))
            db.commit()
        finally:
            db.close()
    except Exception:  # pragma: no cover — usage logging must never break a request
        log.debug("usage ledger write skipped", exc_info=True)


class LLMRouter:
    def complete(
        self,
        role: str,
        system: str,
        user: str,
        *,
        shape: Any | None = None,
        history: list[Message] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        client_id: str | None = None,
    ) -> LLMResult:
        """Run a completion through the role's provider chain.

        `shape` — when given, JSON mode is requested, the shape is appended to
        the prompt as the required output schema, and the reply is parsed.
        """
        messages: list[Message] = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        prompt = user
        if shape is not None:
            prompt += (
                "\n\nRespond ONLY with valid JSON matching exactly this shape "
                "(values shown are type/content hints):\n" + json.dumps(shape, indent=2)
            )
        messages.append({"role": "user", "content": prompt})

        routes = ROLE_ROUTES.get(role, ROLE_ROUTES["default"])
        started = time.time()

        for provider, model_attr in routes:
            if not provider.available():
                continue
            model = getattr(settings, model_attr)
            for attempt in range(settings.LLM_MAX_RETRIES + 1):
                try:
                    res = provider.complete(
                        messages, model=model, json_mode=shape is not None,
                        max_tokens=max_tokens, temperature=temperature,
                    )
                    data = _extract_json(res.text) if shape is not None else None
                    cost = estimate_cost(model, res.tokens_in, res.tokens_out)
                    _record_usage(client_id, res, cost)
                    return LLMResult(
                        text=res.text, data=data, provider=res.provider, model=res.model,
                        tokens_in=res.tokens_in, tokens_out=res.tokens_out, cost_usd=cost,
                        latency_ms=int((time.time() - started) * 1000),
                    )
                except Exception as exc:
                    log.warning("LLM %s/%s attempt %d failed: %s", provider.name, model, attempt + 1, exc)
                    time.sleep(min(2 ** attempt, 4))

        # Final fallback: deterministic mock (always succeeds).
        text = mock.mock_complete(system + "\n" + prompt, shape)
        data = json.loads(text) if shape is not None else None
        return LLMResult(
            text=text, data=data, provider="mock", model="mock",
            tokens_in=len(prompt) // 4, tokens_out=len(text) // 4, cost_usd=0.0,
            latency_ms=int((time.time() - started) * 1000),
        )

    def complete_json(self, role: str, system: str, user: str, shape: Any,
                      **kwargs: Any) -> Any:
        """Convenience: returns parsed JSON directly."""
        return self.complete(role, system, user, shape=shape, **kwargs).data

    def complete_text(self, role: str, system: str, user: str, **kwargs: Any) -> str:
        return self.complete(role, system, user, **kwargs).text


llm = LLMRouter()
