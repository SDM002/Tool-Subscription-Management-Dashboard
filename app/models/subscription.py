"""app/models/subscription.py — subscriptions table."""
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BillingCycle:
    MONTHLY   = "monthly"
    QUARTERLY = "quarterly"
    YEARLY    = "yearly"
    LIFETIME  = "lifetime"
    ALL = [MONTHLY, QUARTERLY, YEARLY, LIFETIME]


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Other")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False, default=BillingCycle.MONTHLY)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship("User", back_populates="subscriptions")  # noqa: F821
    reminder_logs: Mapped[list["ReminderLog"]] = relationship(  # noqa: F821
        "ReminderLog", back_populates="subscription", cascade="all, delete-orphan"
    )

    @property
    def monthly_cost(self) -> float:
        if self.billing_cycle == BillingCycle.MONTHLY:   return self.price
        if self.billing_cycle == BillingCycle.QUARTERLY: return round(self.price / 3, 2)
        if self.billing_cycle == BillingCycle.YEARLY:    return round(self.price / 12, 2)
        return 0.0

    @property
    def yearly_cost(self) -> float:
        if self.billing_cycle == BillingCycle.MONTHLY:   return round(self.price * 12, 2)
        if self.billing_cycle == BillingCycle.QUARTERLY: return round(self.price * 4, 2)
        if self.billing_cycle == BillingCycle.YEARLY:    return self.price
        return self.price
