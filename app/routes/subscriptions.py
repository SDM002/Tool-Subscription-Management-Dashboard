"""app/routes/subscriptions.py — CRUD endpoints, all protected by JWT."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreateRequest, SubscriptionListResponse,
    SubscriptionResponse, SubscriptionUpdateRequest,
)
from app.services.subscription_service import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("", response_model=SubscriptionResponse, status_code=201)
async def create(payload: SubscriptionCreateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await subscription_service.create(db, user.id, payload)


@router.get("", response_model=SubscriptionListResponse)
async def list_all(active_only: bool = Query(False), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await subscription_service.list_all(db, user.id, active_only)


@router.get("/{sub_id}", response_model=SubscriptionResponse)
async def get_one(sub_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await subscription_service.get(db, user.id, sub_id)


@router.patch("/{sub_id}", response_model=SubscriptionResponse)
async def update(sub_id: int, payload: SubscriptionUpdateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await subscription_service.update(db, user.id, sub_id, payload)


@router.delete("/{sub_id}", status_code=204)
async def delete(sub_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await subscription_service.delete(db, user.id, sub_id)
