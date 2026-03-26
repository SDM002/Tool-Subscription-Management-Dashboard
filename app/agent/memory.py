

import logging
import uuid
from datetime import datetime, timezone

import chromadb
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.chat_memory import ChatMemory

logger = logging.getLogger(__name__)

# ── ChromaDB ──────────────────────────────────────────────────
_chroma_client: chromadb.ClientAPI | None = None


def _get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        import os
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client


def _user_collection(user_id: int) -> chromadb.Collection:
    """Each user gets their own isolated ChromaDB collection."""
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=f"{settings.chroma_collection}_user_{user_id}",
        metadata={"hnsw:space": "cosine"},
    )


# ── Short-term: load history as LangChain message objects ─────

SHORT_TERM_WINDOW = 20


async def load_short_term(
    db: AsyncSession, user_id: int, session_id: str, limit: int = SHORT_TERM_WINDOW
) -> list:
    """Return last N messages as HumanMessage / AIMessage objects."""
    result = await db.execute(
        select(ChatMemory)
        .where(ChatMemory.user_id == user_id, ChatMemory.session_id == session_id)
        .order_by(ChatMemory.created_at.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))

    messages = []
    for r in rows:
        if r.role == "human":
            messages.append(HumanMessage(content=r.content))
        elif r.role == "ai":
            messages.append(AIMessage(content=r.content))
        # tool messages are not replayed — they're ephemeral
    return messages


async def save_message(
    db: AsyncSession, user_id: int, session_id: str, role: str, content: str
) -> None:
    """Persist one message (human | ai) to short-term SQL memory."""
    db.add(ChatMemory(
        user_id=user_id, session_id=session_id, role=role, content=content
    ))
    await db.flush()


async def clear_session(db: AsyncSession, user_id: int, session_id: str) -> None:
    await db.execute(
        delete(ChatMemory).where(
            ChatMemory.user_id == user_id,
            ChatMemory.session_id == session_id,
        )
    )


# ── Long-term: ChromaDB ───────────────────────────────────────

async def search_long_term(user_id: int, query: str, n_results: int = 3) -> list[str]:
    """Return semantically similar snippets from past conversations."""
    try:
        col   = _user_collection(user_id)
        count = col.count()
        if count == 0:
            return []
        results = col.query(
            query_texts=[query],
            n_results=min(n_results, count),
        )
        return [d for d in results.get("documents", [[]])[0] if d]
    except Exception as exc:
        logger.warning("Long-term memory search failed: %s", exc)
        return []


async def save_to_long_term(
    user_id: int, session_id: str, content: str, metadata: dict | None = None
) -> None:
    """Store a summary of the exchange in ChromaDB for future retrieval."""
    try:
        col = _user_collection(user_id)
        col.add(
            documents=[content],
            ids=[f"{user_id}_{session_id}_{uuid.uuid4().hex[:8]}"],
            metadatas=[{
                "user_id":    str(user_id),
                "session_id": session_id,
                "timestamp":  datetime.now(timezone.utc).isoformat(),
                **(metadata or {}),
            }],
        )
    except Exception as exc:
        logger.warning("Long-term memory save failed: %s", exc)


def new_session_id() -> str:
    return uuid.uuid4().hex
