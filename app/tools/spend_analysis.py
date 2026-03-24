"""
app/tools/spend_analysis.py  [NEW]

Tool function: get_spending_summary
Returns monthly/yearly totals + per-category breakdown.
"""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription


async def get_spending_summary(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712
        )
    )
    subs = result.scalars().all()

    total_monthly = round(sum(s.monthly_cost for s in subs), 2)
    total_yearly = round(sum(s.yearly_cost for s in subs), 2)

    by_category: dict[str, dict] = defaultdict(
        lambda: {"monthly": 0.0, "yearly": 0.0, "tools": []}
    )
    for s in subs:
        by_category[s.category]["monthly"] += s.monthly_cost
        by_category[s.category]["yearly"] += s.yearly_cost
        by_category[s.category]["tools"].append(s.tool_name)

    return {
        "active_count": len(subs),
        "total_monthly": total_monthly,
        "total_yearly": total_yearly,
        "by_category": [
            {
                "category": cat,
                "monthly": round(v["monthly"], 2),
                "yearly": round(v["yearly"], 2),
                "tools": v["tools"],
            }
            for cat, v in sorted(
                by_category.items(), key=lambda x: x[1]["monthly"], reverse=True
            )
        ],
    }


async def get_subscriptions(db: AsyncSession, user_id: int) -> dict:
    """Return all active subscriptions as a list."""
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712
        )
    )
    subs = result.scalars().all()

    return {
        "count": len(subs),
        "subscriptions": [
            {
                "id": s.id,
                "tool_name": s.tool_name,
                "category": s.category,
                "price": s.price,
                "currency": s.currency,
                "billing_cycle": s.billing_cycle,
                "renewal_date": s.renewal_date.isoformat() if s.renewal_date else None,
                "monthly_cost": s.monthly_cost,
                "yearly_cost": s.yearly_cost,
                "notes": s.notes,
            }
            for s in sorted(subs, key=lambda x: x.tool_name)
        ],
    }


async def get_subscription_by_name(
    db: AsyncSession, user_id: int, name: str
) -> dict:
    """Look up a subscription by tool name (case-insensitive partial match)."""
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712
        )
    )
    subs = result.scalars().all()

    name_lower = name.lower()
    matches = [s for s in subs if name_lower in s.tool_name.lower()]

    if not matches:
        return {"found": False, "message": f"No subscription matching '{name}' found."}

    return {
        "found": True,
        "matches": [
            {
                "id": s.id,
                "tool_name": s.tool_name,
                "category": s.category,
                "price": s.price,
                "currency": s.currency,
                "billing_cycle": s.billing_cycle,
                "renewal_date": s.renewal_date.isoformat() if s.renewal_date else None,
                "monthly_cost": s.monthly_cost,
                "yearly_cost": s.yearly_cost,
                "notes": s.notes,
            }
            for s in matches
        ],
    }
