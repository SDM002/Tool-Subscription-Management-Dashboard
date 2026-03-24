"""
app/models/chat_memory.py  [NEW]

Stores per-user short-term conversation history in the SQL DB.
Long-term semantic memory is handled separately via ChromaDB.

Each row is one message (role: user | assistant | tool).
The `session_id` groups messages into logical conversations.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ChatMemory(Base):
    __tablename__ = "chat_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user | assistant | tool
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="chat_memories")  # noqa: F821

    def __repr__(self) -> str:
        snippet = self.content[:40].replace("\n", " ")
        return f"<ChatMemory id={self.id} role={self.role!r} session={self.session_id!r} msg={snippet!r}>"
