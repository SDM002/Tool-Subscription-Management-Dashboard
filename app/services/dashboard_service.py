"""
app/services/dashboard_service.py  [NEW]

Computes all dashboard metrics for a user:
  - total monthly / yearly spend
  - subscriptions due this week / this month
  - spend breakdown by category
All queries are scoped to user_id for data isolation.
"""

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.services.dashboard import (
    DashboardSummaryResponse,
    RenewalItem,
    SpendByCategoryItem,
)


class DashboardService:

    async def get_summary(
        self, db: AsyncSession, user_id: int
    ) -> DashboardSummaryResponse:
        # Fetch all subscriptions for this user
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        all_subs = result.scalars().all()
        active_subs = [s for s in all_subs if s.is_active]

        today = date.today()
        week_end = today + timedelta(days=7)
        month_end = today + timedelta(days=30)

        # ── Spending totals ───────────────────────────────────
        total_monthly = round(sum(s.monthly_cost for s in active_subs), 2)
        total_yearly = round(sum(s.yearly_cost for s in active_subs), 2)

        # ── Renewal lists ─────────────────────────────────────
        due_week: list[RenewalItem] = []
        due_month: list[RenewalItem] = []

        for sub in active_subs:
            if sub.renewal_date is None:
                continue
            days_left = (sub.renewal_date - today).days
            if sub.renewal_date < today:
                # Overdue — still show it
                days_left = (sub.renewal_date - today).days  # negative

            item = RenewalItem(
                id=sub.id,
                tool_name=sub.tool_name,
                category=sub.category,
                renewal_date=sub.renewal_date,
                days_until_renewal=days_left,
                price=sub.price,
                billing_cycle=sub.billing_cycle,
                currency=sub.currency,
            )

            if today <= sub.renewal_date <= week_end:
                due_week.append(item)
            if today <= sub.renewal_date <= month_end:
                due_month.append(item)

        # Sort by soonest first
        due_week.sort(key=lambda x: x.renewal_date)
        due_month.sort(key=lambda x: x.renewal_date)

        # ── Spend by category ─────────────────────────────────
        cat_map: dict[str, dict] = defaultdict(
            lambda: {"monthly": 0.0, "yearly": 0.0, "count": 0}
        )
        for sub in active_subs:
            cat_map[sub.category]["monthly"] += sub.monthly_cost
            cat_map[sub.category]["yearly"] += sub.yearly_cost
            cat_map[sub.category]["count"] += 1

        spend_by_cat = [
            SpendByCategoryItem(
                category=cat,
                monthly_cost=round(vals["monthly"], 2),
                yearly_cost=round(vals["yearly"], 2),
                count=vals["count"],
            )
            for cat, vals in sorted(
                cat_map.items(), key=lambda x: x[1]["monthly"], reverse=True
            )
        ]

        return DashboardSummaryResponse(
            total_subscriptions=len(all_subs),
            active_subscriptions=len(active_subs),
            total_monthly_spend=total_monthly,
            total_yearly_spend=total_yearly,
            due_this_week=due_week,
            due_this_month=due_month,
            spend_by_category=spend_by_cat,
        )

    async def get_upcoming_renewals(
        self, db: AsyncSession, user_id: int, days: int = 30
    ) -> list[RenewalItem]:
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
            RenewalItem(
                id=s.id,
                tool_name=s.tool_name,
                category=s.category,
                renewal_date=s.renewal_date,
                days_until_renewal=(s.renewal_date - today).days,
                price=s.price,
                billing_cycle=s.billing_cycle,
                currency=s.currency,
            )
            for s in sorted(subs, key=lambda x: x.renewal_date)
        ]
        return items


dashboard_service = DashboardService()
