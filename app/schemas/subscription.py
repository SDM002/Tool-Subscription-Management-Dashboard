from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models.subscription import BillingCycle


class SubscriptionCreateRequest(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="Other", max_length=100)
    start_date: Optional[date] = None
    renewal_date: Optional[date] = None
    billing_cycle: str = Field(default=BillingCycle.MONTHLY)
    price: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", max_length=10)
    website_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None
    is_active: bool = True

    @field_validator("billing_cycle")
    @classmethod
    def validate_cycle(cls, v: str) -> str:
        if v not in BillingCycle.ALL:
            raise ValueError(f"billing_cycle must be one of {BillingCycle.ALL}")
        return v


class SubscriptionUpdateRequest(BaseModel):
    tool_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    renewal_date: Optional[date] = None
    billing_cycle: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0.0)
    currency: Optional[str] = Field(default=None, max_length=10)
    website_url: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("billing_cycle")
    @classmethod
    def validate_cycle(cls, v: str | None) -> str | None:
        if v is not None and v not in BillingCycle.ALL:
            raise ValueError(f"billing_cycle must be one of {BillingCycle.ALL}")
        return v


class SubscriptionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    user_id: int
    tool_name: str
    category: str
    start_date: Optional[date]
    renewal_date: Optional[date]
    billing_cycle: str
    price: float
    currency: str
    website_url: Optional[str]
    notes: Optional[str]
    is_active: bool
    monthly_cost: float
    yearly_cost: float
    created_at: datetime
    updated_at: datetime


class SubscriptionListResponse(BaseModel):
    total: int
    subscriptions: list[SubscriptionResponse]
