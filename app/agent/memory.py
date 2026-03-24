"""
app/agent/memory.py  [NEW]

Two-layer memory for the AI assistant:

SHORT-TERM  — SQL table (chat_memories)
  • Last N messages in a session, retrieved per conversation turn.
  • Stored per (user_id, session_id).

LONG-TERM   — ChromaDB vector store
  • Semantically meaningful facts extracted from conversations.
  • Searched by similarity at the start of each turn to inject
    relevant context from past sessions.
  • Stored per user_id (collection namespace).
"""

import logging
import uuid
from datetime import datetime, timezone

import chromadb
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.chat_memory import ChatMemory

logger = logging.getLogger(__name__)

# ── ChromaDB client (persistent) ─────────────────────────────
_chroma_client: chromadb.ClientAPI | None = None


def _get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        import os
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client


def _get_user_collection(user_id: int) -> chromadb.Collection:
    """Each user gets their own ChromaDB collection for data isolation."""
    client = _get_chroma_client()
    collection_name = f"{settings.chroma_collection}_user_{user_id}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


# ── Short-term memory (SQL) ───────────────────────────────────

SHORT_TERM_WINDOW = 20  # max messages to include in context


async def load_short_term(
    db: AsyncSession,
    user_id: int,
    session_id: str,
    limit: int = SHORT_TERM_WINDOW,
) -> list[dict]:
    """Load the last `limit` messages for a session as {role, content} dicts."""
    result = await db.execute(
        select(ChatMemory)
        .where(
            ChatMemory.user_id == user_id,
            ChatMemory.session_id == session_id,
        )
        .order_by(ChatMemory.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    # Reverse so oldest is first (chronological order for the LLM)
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


async def save_message(
    db: AsyncSession,
    user_id: int,
    session_id: str,
    role: str,
    content: str,
) -> None:
    """Persist a single message to short-term SQL memory."""
    msg = ChatMemory(
        user_id=user_id,
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(msg)
    await db.flush()


async def clear_session(
    db: AsyncSession, user_id: int, session_id: str
) -> None:
    """Delete all messages in a session (e.g. 'start new chat')."""
    await db.execute(
        delete(ChatMemory).where(
            ChatMemory.user_id == user_id,
            ChatMemory.session_id == session_id,
        )
    )


# ── Long-term memory (ChromaDB) ───────────────────────────────

async def search_long_term(
    user_id: int, query: str, n_results: int = 3
) -> list[str]:
    """
    Semantically search past conversation facts.
    Returns a list of relevant text snippets to inject as context.
    """
    try:
        collection = _get_user_collection(user_id)
        count = collection.count()
        if count == 0:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
        )
        docs = results.get("documents", [[]])[0]
        return [d for d in docs if d]
    except Exception as exc:
        logger.warning("Long-term memory search failed: %s", exc)
        return []


async def save_to_long_term(
    user_id: int,
    session_id: str,
    content: str,
    metadata: dict | None = None,
) -> None:
    """
    Store a fact or summary in ChromaDB for long-term retrieval.
    Called after assistant replies with meaningful content.
    """
    try:
        collection = _get_user_collection(user_id)
        doc_id = f"{user_id}_{session_id}_{uuid.uuid4().hex[:8]}"
        collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[
                {
                    "user_id": str(user_id),
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **(metadata or {}),
                }
            ],
        )
    except Exception as exc:
        logger.warning("Failed to save to long-term memory: %s", exc)


def generate_session_id() -> str:
    """Generate a new unique session ID."""
    return uuid.uuid4().hex
