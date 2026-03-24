"""
app/schemas/dashboard.py  [NEW]

Pydantic schemas for the dashboard summary endpoint.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel


class RenewalItem(BaseModel):
    """A subscription that's coming up for renewal."""
    id: int
    tool_name: str
    category: str
    renewal_date: date
    days_until_renewal: int
    price: float
    billing_cycle: str
    currency: str


class SpendByCategoryItem(BaseModel):
    category: str
    monthly_cost: float
    yearly_cost: float
    count: int


class DashboardSummaryResponse(BaseModel):
    total_subscriptions: int
    active_subscriptions: int

    # Spending
    total_monthly_spend: float
    total_yearly_spend: float

    # Renewals
    due_this_week: list[RenewalItem]
    due_this_month: list[RenewalItem]

    # Breakdown
    spend_by_category: list[SpendByCategoryItem]

    # Currency (for display)
    currency: str = "USD"
