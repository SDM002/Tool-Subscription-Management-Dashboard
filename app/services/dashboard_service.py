"""app/services/dashboard_service.py — spending totals and renewal calculations."""
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.schemas.dashboard import DashboardSummaryResponse, RenewalItem, SpendByCategoryItem


class DashboardService:

    async def get_summary(self, db: AsyncSession, user_id: int) -> DashboardSummaryResponse:
        result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        all_subs = result.scalars().all()
        active = [s for s in all_subs if s.is_active]

        today = date.today()
        week_end  = today + timedelta(days=7)
        month_end = today + timedelta(days=30)

        total_monthly = round(sum(s.monthly_cost for s in active), 2)
        total_yearly  = round(sum(s.yearly_cost  for s in active), 2)

        due_week:  list[RenewalItem] = []
        due_month: list[RenewalItem] = []

        for s in active:
            if s.renewal_date is None:
                continue
            days_left = (s.renewal_date - today).days
            item = RenewalItem(
                id=s.id, tool_name=s.tool_name, category=s.category,
                renewal_date=s.renewal_date, days_until_renewal=days_left,
                price=s.price, billing_cycle=s.billing_cycle, currency=s.currency,
            )
            if today <= s.renewal_date <= week_end:
                due_week.append(item)
            if today <= s.renewal_date <= month_end:
                due_month.append(item)

        due_week.sort(key=lambda x: x.renewal_date)
        due_month.sort(key=lambda x: x.renewal_date)

        cat_map: dict[str, dict] = defaultdict(lambda: {"monthly": 0.0, "yearly": 0.0, "count": 0})
        for s in active:
            cat_map[s.category]["monthly"] += s.monthly_cost
            cat_map[s.category]["yearly"]  += s.yearly_cost
            cat_map[s.category]["count"]   += 1

        spend_by_cat = [
            SpendByCategoryItem(
                category=cat,
                monthly_cost=round(v["monthly"], 2),
                yearly_cost=round(v["yearly"], 2),
                count=v["count"],
            )
            for cat, v in sorted(cat_map.items(), key=lambda x: x[1]["monthly"], reverse=True)
        ]

        return DashboardSummaryResponse(
            total_subscriptions=len(all_subs),
            active_subscriptions=len(active),
            total_monthly_spend=total_monthly,
            total_yearly_spend=total_yearly,
            due_this_week=due_week,
            due_this_month=due_month,
            spend_by_category=spend_by_cat,
        )

    async def get_upcoming_renewals(self, db: AsyncSession, user_id: int, days: int = 30) -> list[RenewalItem]:
        today = date.today()
        end   = today + timedelta(days=days)
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,  # noqa: E712
                Subscription.renewal_date >= today,
                Subscription.renewal_date <= end,
            )
        )
        subs = result.scalars().all()
        return [
            RenewalItem(
                id=s.id, tool_name=s.tool_name, category=s.category,
                renewal_date=s.renewal_date,
                days_until_renewal=(s.renewal_date - today).days,
                price=s.price, billing_cycle=s.billing_cycle, currency=s.currency,
            )
            for s in sorted(subs, key=lambda x: x.renewal_date)
        ]


dashboard_service = DashboardService()
