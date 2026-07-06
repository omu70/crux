"""Application configuration, loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — empty string falls back to a local SQLite file.
    DATABASE_URL: str = ""

    # Auth / JWT
    JWT_SECRET: str = "dev-insecure-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    RATE_LIMIT_PER_MINUTE: int = 120

    # Seed admin
    SEED_ADMIN_USERNAME: str = "Dizigroww"
    SEED_ADMIN_PASSWORD: str = "Dizigroww@2026"
    SEED_ADMIN_EMAIL: str = "admin@dizigroww.com"

    # Supabase
    SUPABASE_URL: str = "https://kiupgoucjytmuxygblps.supabase.co"
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "crux-documents"

    # Third-party APIs
    GEMINI_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "[email protected]"
    META_ACCESS_TOKEN: str = ""
    SHOPIFY_STORE_DOMAIN: str = ""
    SHOPIFY_ADMIN_TOKEN: str = ""
    WOOCOMMERCE_URL: str = ""
    WOOCOMMERCE_KEY: str = ""
    WOOCOMMERCE_SECRET: str = ""
    GA4_PROPERTY_ID: str = ""
    SEARCH_CONSOLE_SITE_URL: str = ""

    # ── Aether AI ─────────────────────────────────────────────────────────────
    # LLM providers (any subset; the router falls back across them, then to
    # deterministic mock mode so every feature works without keys).
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    # GEMINI_API_KEY reused from above.
    LLM_DEFAULT_MODEL: str = "gpt-4o"
    LLM_FAST_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIM: int = 1024  # requested dims for text-embedding-3-large
    LLM_TIMEOUT_SECONDS: int = 90
    LLM_MAX_RETRIES: int = 2
    AETHER_FORCE_MOCK: bool = False  # force mock AI even if keys exist (tests)

    # Meta Marketing API (publishing)
    META_AD_ACCOUNT_ID: str = ""     # act_XXXX
    META_PAGE_ID: str = ""
    META_PIXEL_ID: str = ""
    META_API_VERSION: str = "v21.0"

    # Celery / Redis (empty broker → tasks run eagerly in-process)
    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Stripe billing
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_GROWTH: str = ""
    STRIPE_PRICE_SCALE: str = ""

    # Observability
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://us.i.posthog.com"

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    @property
    def sqlalchemy_url(self) -> str:
        """Resolve the DB URL, defaulting to a local SQLite file for dev/tests."""
        url = (self.DATABASE_URL or "").strip()
        if not url:
            return "sqlite:///./crux.db"
        # Normalise Supabase/Heroku-style `postgres://` to the psycopg2 driver.
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        if url.startswith(("postgresql+psycopg2://", "sqlite")):
            return url
        # Misconfiguration (e.g. the Supabase https:// project URL pasted by mistake).
        # Don't crash the service — fall back to SQLite and log the exact fix.
        import logging
        logging.getLogger("crux").error(
            "DATABASE_URL=%r is not a postgresql:// or sqlite URL. Falling back to "
            "temporary SQLite. Use the Supabase 'Session pooler' connection string "
            "(starts with postgresql://) for a persistent database.", url,
        )
        return "sqlite:///./crux.db"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.sqlalchemy_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
