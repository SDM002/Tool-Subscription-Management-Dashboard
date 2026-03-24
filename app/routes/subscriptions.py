"""
app/routes/subscriptions.py  [NEW]

Subscription CRUD endpoints. All protected by JWT.
User isolation is enforced in the service layer.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreateRequest,
    SubscriptionListResponse,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)
from app.services.subscription_service import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    payload: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """Add a new subscription for the current user."""
    return await subscription_service.create(db, current_user.id, payload)


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    active_only: bool = Query(False, description="Return only active subscriptions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionListResponse:
    """List all subscriptions belonging to the current user."""
    return await subscription_service.list_all(db, current_user.id, active_only)


@router.get("/{sub_id}", response_model=SubscriptionResponse)
async def get_subscription(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """Get a single subscription by ID."""
    return await subscription_service.get(db, current_user.id, sub_id)


@router.patch("/{sub_id}", response_model=SubscriptionResponse)
async def update_subscription(
    sub_id: int,
    payload: SubscriptionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """Partially update a subscription (PATCH semantics)."""
    return await subscription_service.update(db, current_user.id, sub_id, payload)


@router.delete("/{sub_id}", status_code=204)
async def delete_subscription(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a subscription permanently."""
    await subscription_service.delete(db, current_user.id, sub_id)
