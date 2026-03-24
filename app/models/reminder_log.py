"""
app/models/reminder_log.py  [NEW]

Tracks which reminder emails have been sent for each subscription
renewal cycle — prevents duplicate reminders from the scheduler.
"""

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    renewal_date: Mapped[date] = mapped_column(Date, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    status: Mapped[str] = mapped_column(
        String(20), default="sent"
    )  # sent | failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="reminder_logs")  # noqa: F821
    subscription: Mapped["Subscription"] = relationship(  # noqa: F821
        "Subscription", back_populates="reminder_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<ReminderLog id={self.id} sub_id={self.subscription_id} "
            f"renewal={self.renewal_date} status={self.status!r}>"
        )
