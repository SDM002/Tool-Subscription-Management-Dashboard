"""
app/core/config.py
All settings loaded from .env — one place, no scattered os.getenv() calls.
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

    # App
    app_name: str = "Subscription Dashboard"
    debug: bool = True

    # Groq — YOUR LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Security
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/subscriptions.db"

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Subscription Dashboard"
    smtp_tls: bool = True

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "subscription_memory"

    # Reminders
    reminder_days_before: int = 7
    reminder_check_interval_hours: int = 24


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
