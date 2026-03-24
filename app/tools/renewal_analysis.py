"""
app/tools/renewal_analysis.py  [NEW]

Tool function: get_upcoming_renewals
Returns a structured summary of subscriptions renewing soon.
Called by the assistant via function calling.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription


async def get_upcoming_renewals(
    db: AsyncSession, user_id: int, days: int = 30
) -> dict:
    """
    Return subscriptions renewing within the next `days` days.
    """
    today = date.today()
    end_date = today + timedelta(days=days)

    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712
            Subscription.renewal_date >= today,
            Subscription.renewal_date <= end_date,
        )
    )
    subs = result.scalars().all()

    items = [
        {
            "id": s.id,
            "tool_name": s.tool_name,
            "category": s.category,
            "renewal_date": s.renewal_date.isoformat() if s.renewal_date else None,
            "days_until_renewal": (s.renewal_date - today).days,
            "price": s.price,
            "currency": s.currency,
            "billing_cycle": s.billing_cycle,
        }
        for s in sorted(subs, key=lambda x: x.renewal_date)
    ]

    return {
        "window_days": days,
        "count": len(items),
        "renewals": items,
    }
