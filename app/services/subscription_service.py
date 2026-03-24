"""
app/services/subscription_service.py  [NEW]

CRUD operations for subscriptions.
All queries are scoped to user_id — enforcing data isolation at the
service layer (not just the route layer).
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.services.subscription import (
    SubscriptionCreateRequest,
    SubscriptionListResponse,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)


class SubscriptionService:

    # ── Create ────────────────────────────────────────────────
    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        payload: SubscriptionCreateRequest,
    ) -> SubscriptionResponse:
        sub = Subscription(user_id=user_id, **payload.model_dump())
        db.add(sub)
        await db.flush()
        await db.refresh(sub)
        return SubscriptionResponse.model_validate(sub)

    # ── List ──────────────────────────────────────────────────
    async def list_all(
        self,
        db: AsyncSession,
        user_id: int,
        active_only: bool = False,
    ) -> SubscriptionListResponse:
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

    # ── Get one ───────────────────────────────────────────────
    async def get(
        self, db: AsyncSession, user_id: int, sub_id: int
    ) -> SubscriptionResponse:
        sub = await self._get_or_404(db, user_id, sub_id)
        return SubscriptionResponse.model_validate(sub)

    # ── Update (PATCH) ────────────────────────────────────────
    async def update(
        self,
        db: AsyncSession,
        user_id: int,
        sub_id: int,
        payload: SubscriptionUpdateRequest,
    ) -> SubscriptionResponse:
        sub = await self._get_or_404(db, user_id, sub_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sub, field, value)
        await db.flush()
        await db.refresh(sub)
        return SubscriptionResponse.model_validate(sub)

    # ── Delete ────────────────────────────────────────────────
    async def delete(
        self, db: AsyncSession, user_id: int, sub_id: int
    ) -> None:
        sub = await self._get_or_404(db, user_id, sub_id)
        await db.delete(sub)
        await db.flush()

    # ── Internal helper ───────────────────────────────────────
    async def _get_or_404(
        self, db: AsyncSession, user_id: int, sub_id: int
    ) -> Subscription:
        result = await db.execute(
            select(Subscription).where(
                Subscription.id == sub_id,
                Subscription.user_id == user_id,   # ← isolation enforced here
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription {sub_id} not found",
            )
        return sub


subscription_service = SubscriptionService()
