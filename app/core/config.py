"""
app/core/config.py  [NEW]

Centralized configuration loaded from environment variables / .env file.
All other modules import `settings` from here — no bare os.getenv() calls
scattered across the codebase.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────
    app_name: str = "Tool Subscription Dashboard"
    app_env: str = "development"
    debug: bool = True

    # ── Security ─────────────────────────────────────────────
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ── Database ─────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./data/subscriptions.db"

    # ── Email ─────────────────────────────────────────────────
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Subscription Dashboard"
    smtp_tls: bool = True

    # ── LLM ──────────────────────────────────────────────────
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"
    llm_max_tokens: int = 2048

    # ── ChromaDB ─────────────────────────────────────────────
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "subscription_memory"

    # ── Reminders ────────────────────────────────────────────
    reminder_days_before: int = 7
    reminder_check_interval_hours: int = 24


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — loaded once at startup."""
    return Settings()


# Module-level singleton for convenience
settings = get_settings()
