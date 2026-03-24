"""
app/schemas/chat.py  [NEW]
Pydantic schemas for the AI assistant chat endpoint.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None   # None → server generates one


class ChatMessageResponse(BaseModel):
    role: str               # user | assistant
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    messages: list[ChatMessageResponse] = []


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageResponse]
