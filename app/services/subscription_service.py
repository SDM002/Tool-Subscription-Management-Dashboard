"""app/services/subscription_service.py — CRUD with user isolation enforced on every query."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.schemas.subscription import (
    SubscriptionCreateRequest, SubscriptionListResponse,
    SubscriptionResponse, SubscriptionUpdateRequest,
)


class SubscriptionService:

    async def create(self, db: AsyncSession, user_id: int, payload: SubscriptionCreateRequest) -> SubscriptionResponse:
        sub = Subscription(user_id=user_id, **payload.model_dump())
        db.add(sub)
        await db.flush()
        await db.refresh(sub)
        return SubscriptionResponse.model_validate(sub)

    async def list_all(self, db: AsyncSession, user_id: int, active_only: bool = False) -> SubscriptionListResponse:
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        if active_only:
            stmt = stmt.where(Subscription.is_active == True)  # noqa: E712
        stmt = stmt.order_by(Subscription.renewal_date.asc().nullslast())
        result = await db.execute(stmt)
        subs = result.scalars().all()
        return SubscriptionListResponse(
            total=len(subs),
            subscriptions=[SubscriptionResponse.model_validate(s) for s in subs],
        )

    async def get(self, db: AsyncSession, user_id: int, sub_id: int) -> SubscriptionResponse:
        sub = await self._get_or_404(db, user_id, sub_id)
        return SubscriptionResponse.model_validate(sub)

    async def update(self, db: AsyncSession, user_id: int, sub_id: int, payload: SubscriptionUpdateRequest) -> SubscriptionResponse:
        sub = await self._get_or_404(db, user_id, sub_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(sub, field, value)
        await db.flush()
        await db.refresh(sub)
        return SubscriptionResponse.model_validate(sub)

    async def delete(self, db: AsyncSession, user_id: int, sub_id: int) -> None:
        sub = await self._get_or_404(db, user_id, sub_id)
        await db.delete(sub)

    async def _get_or_404(self, db: AsyncSession, user_id: int, sub_id: int) -> Subscription:
        result = await db.execute(
            select(Subscription).where(
                Subscription.id == sub_id,
                Subscription.user_id == user_id,  # ← isolation
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            raise HTTPException(status_code=404, detail=f"Subscription {sub_id} not found")
        return sub


subscription_service = SubscriptionService()
