from dataclasses import dataclass, field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import BillingCycle, Subscription


@dataclass
class InsightItem:
    type: str          # duplicate | high_cost | annual_saving | summary
    title: str
    detail: str
    affected_tools: list[str] = field(default_factory=list)
    potential_saving: float = 0.0


class PricingService:

    async def get_insights(
        self, db: AsyncSession, user_id: int
    ) -> list[InsightItem]:
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True,  # noqa: E712
            )
        )
        subs = result.scalars().all()

        if not subs:
            return []

        insights: list[InsightItem] = []

        insights += self._detect_duplicates(subs)
        insights += self._detect_annual_savings(subs)
        insights += self._detect_high_cost(subs)
        insights += self._spending_summary(subs)

        return insights

    # ── Duplicate detection ───────────────────────────────────
    def _detect_duplicates(self, subs: list[Subscription]) -> list[InsightItem]:
        from collections import defaultdict
        category_map: dict[str, list[str]] = defaultdict(list)
        for s in subs:
            category_map[s.category].append(s.tool_name)

        insights = []
        for category, tools in category_map.items():
            if len(tools) >= 2:
                insights.append(
                    InsightItem(
                        type="duplicate",
                        title=f"Multiple tools in '{category}'",
                        detail=(
                            f"You have {len(tools)} tools in the '{category}' category: "
                            f"{', '.join(tools)}. Consider consolidating to reduce overlap."
                        ),
                        affected_tools=tools,
                    )
                )
        return insights

    # ── Annual billing savings ────────────────────────────────
    def _detect_annual_savings(self, subs: list[Subscription]) -> list[InsightItem]:
        insights = []
        for s in subs:
            if s.billing_cycle == BillingCycle.MONTHLY and s.price > 5:
                # Typical annual discount is ~16-20%
                annual_if_monthly = s.price * 12
                estimated_annual_price = round(annual_if_monthly * 0.83, 2)
                saving = round(annual_if_monthly - estimated_annual_price, 2)
                insights.append(
                    InsightItem(
                        type="annual_saving",
                        title=f"Switch '{s.tool_name}' to annual billing",
                        detail=(
                            f"Paying {s.currency} {s.price}/month = "
                            f"{s.currency} {annual_if_monthly:.2f}/year. "
                            f"Annual plans typically save ~17% "
                            f"(≈ {s.currency} {saving:.2f}/year)."
                        ),
                        affected_tools=[s.tool_name],
                        potential_saving=saving,
                    )
                )
        # Sort by highest potential saving first
        insights.sort(key=lambda x: x.potential_saving, reverse=True)
        return insights[:5]  # top 5 only

    # ── High-cost alerts ──────────────────────────────────────
    def _detect_high_cost(self, subs: list[Subscription]) -> list[InsightItem]:
        insights = []
        for s in subs:
            if s.monthly_cost > 50:
                insights.append(
                    InsightItem(
                        type="high_cost",
                        title=f"High spend on '{s.tool_name}'",
                        detail=(
                            f"'{s.tool_name}' costs {s.currency} {s.monthly_cost:.2f}/month "
                            f"({s.currency} {s.yearly_cost:.2f}/year). "
                            "Review whether all features are being used."
                        ),
                        affected_tools=[s.tool_name],
                    )
                )
        return insights

    # ── Overall summary ───────────────────────────────────────
    def _spending_summary(self, subs: list[Subscription]) -> list[InsightItem]:
        total_monthly = sum(s.monthly_cost for s in subs)
        total_yearly = sum(s.yearly_cost for s in subs)
        return [
            InsightItem(
                type="summary",
                title="Total subscription spend",
                detail=(
                    f"You have {len(subs)} active subscriptions costing "
                    f"${total_monthly:.2f}/month (${total_yearly:.2f}/year)."
                ),
            )
        ]


pricing_service = PricingService()
