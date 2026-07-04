"""Lightweight in-memory fixed-window rate limiter (dependency-free).

For a single-process deployment this is sufficient. Behind multiple workers,
swap the store for Redis — the middleware interface stays the same.
"""
from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit_per_minute: int = 120):
        super().__init__(app)
        self.limit = limit_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit the API surface, not docs/health.
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path.split('/')[2] if len(request.url.path.split('/')) > 2 else ''}"
        now = time.time()
        window_start = now - 60

        hits = [t for t in self._hits[key] if t > window_start]
        if len(hits) >= self.limit:
            retry = int(60 - (now - hits[0])) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)
        self._hits[key] = hits
        return await call_next(request)
