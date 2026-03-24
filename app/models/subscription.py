"""
app/models/subscription.py  [NEW]

SQLAlchemy ORM model for tool subscriptions.
Each subscription belongs to exactly one user (user_id FK).
"""

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BillingCycle:
    """String constants for billing cycle values."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"

    ALL = [MONTHLY, QUARTERLY, YEARLY, LIFETIME]


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Ownership ─────────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Core fields ───────────────────────────────────────────
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Other")

    # Dates
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Billing
    billing_cycle: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BillingCycle.MONTHLY
    )
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")

    # Extras
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Metadata ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")  # noqa: F821
    reminder_logs: Mapped[list["ReminderLog"]] = relationship(  # noqa: F821
        "ReminderLog",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )

    # ── Computed helpers ──────────────────────────────────────
    @property
    def monthly_cost(self) -> float:
        """Normalize price to a monthly equivalent."""
        if self.billing_cycle == BillingCycle.MONTHLY:
            return self.price
        elif self.billing_cycle == BillingCycle.QUARTERLY:
            return round(self.price / 3, 2)
        elif self.billing_cycle == BillingCycle.YEARLY:
            return round(self.price / 12, 2)
        return 0.0  # lifetime — no recurring cost

    @property
    def yearly_cost(self) -> float:
        """Normalize price to a yearly equivalent."""
        if self.billing_cycle == BillingCycle.MONTHLY:
            return round(self.price * 12, 2)
        elif self.billing_cycle == BillingCycle.QUARTERLY:
            return round(self.price * 4, 2)
        elif self.billing_cycle == BillingCycle.YEARLY:
            return self.price
        return self.price  # lifetime — show as-is

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} tool={self.tool_name!r} user_id={self.user_id}>"
