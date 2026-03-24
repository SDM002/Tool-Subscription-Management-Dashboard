"""
app/core/database.py  [NEW]

Async SQLAlchemy engine + session factory.
Uses SQLite now, but DATABASE_URL can be swapped to PostgreSQL without
touching any other file — just change the URL and install asyncpg.

Pattern used throughout the app:
    async with get_db() as db:
        result = await db.execute(...)
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ── Base class for all ORM models ────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Engine ───────────────────────────────────────────────────
# echo=True logs all SQL in dev — turn off in production
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    # SQLite-specific: required for async multi-thread access
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.database_url
    else {},
)

# ── Session factory ──────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep objects usable after commit
    autoflush=False,
    autocommit=False,
)


# ── Dependency for FastAPI routes ────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.
    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Context manager variant (for services/background tasks) ──
@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Use this outside of FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables on startup if they don't exist."""
    # Ensure the data directory exists
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables — used in tests only."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
