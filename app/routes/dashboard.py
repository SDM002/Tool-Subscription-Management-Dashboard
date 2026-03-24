from datetime import date
from pydantic import BaseModel


class RenewalItem(BaseModel):
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
    total_monthly_spend: float
    total_yearly_spend: float
    due_this_week: list[RenewalItem]
    due_this_month: list[RenewalItem]
    spend_by_category: list[SpendByCategoryItem]
