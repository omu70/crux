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
    SEED_ADMIN_USERNAME: str = "admin"
    SEED_ADMIN_PASSWORD: str = "Admin@12345"
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

    @property
    def sqlalchemy_url(self) -> str:
        """Resolve the DB URL, defaulting to a local SQLite file for dev/tests."""
        if self.DATABASE_URL:
            # Normalise Supabase/Heroku-style `postgres://` to the psycopg2 driver.
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
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
