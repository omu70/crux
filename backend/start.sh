#!/usr/bin/env sh
# CRUX backend entrypoint — seed demo data (idempotent), then serve the API.
# Binds the platform-provided $PORT (Render sets this; defaults to 8000 locally).

python -m app.seed || echo "[start] seed skipped/failed — continuing"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
