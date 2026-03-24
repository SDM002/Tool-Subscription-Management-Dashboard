"""
app/routes/chat.py  [NEW]

AI assistant chat endpoints:
  POST /api/chat          → send message, get reply
  GET  /api/chat/history  → load session message history
  DELETE /api/chat/session → clear a session
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.assistant_service import assistant_service
from app.agent.memory import clear_session, load_short_term
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.chat_memory import ChatMemory
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/chat", tags=["AI Assistant"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Send a message to the AI assistant.
    Returns the assistant's reply and the session_id.
    """
    reply, session_id = await assistant_service.chat(
        db=db,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        user_message=payload.message,
        session_id=payload.session_id,
    )

    # Load updated history (last 10 messages for the response)
    history = await load_short_term(db, current_user.id, session_id, limit=10)

    # Fetch timestamps from DB for the response shape
    result = await db.execute(
        select(ChatMemory)
        .where(
            ChatMemory.user_id == current_user.id,
            ChatMemory.session_id == session_id,
        )
        .order_by(ChatMemory.created_at.desc())
        .limit(10)
    )
    rows = list(reversed(result.scalars().all()))

    messages = [
        ChatMessageResponse(
            role=r.role,
            content=r.content,
            created_at=r.created_at,
        )
        for r in rows
    ]

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        messages=messages,
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    """Load full message history for a session."""
    result = await db.execute(
        select(ChatMemory)
        .where(
            ChatMemory.user_id == current_user.id,
            ChatMemory.session_id == session_id,
        )
        .order_by(ChatMemory.created_at.asc())
    )
    rows = result.scalars().all()

    return ChatHistoryResponse(
        session_id=session_id,
        messages=[
            ChatMessageResponse(
                role=r.role,
                content=r.content,
                created_at=r.created_at,
            )
            for r in rows
        ],
    )


@router.delete("/session", response_model=MessageResponse)
async def clear_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Clear all messages in a session (start fresh)."""
    await clear_session(db, current_user.id, session_id)
    return MessageResponse(message=f"Session {session_id} cleared.")
