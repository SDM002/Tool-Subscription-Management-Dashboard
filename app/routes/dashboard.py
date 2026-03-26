import asyncio
import functools
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse, RenewalItem
from app.services.dashboard_service import dashboard_service
from app.services.reminder_service import reminder_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await dashboard_service.get_summary(db, user.id)


@router.get("/renewals", response_model=list[RenewalItem])
async def renewals(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await dashboard_service.get_upcoming_renewals(db, user.id, days)


@router.get("/insights")
async def insights(user: User = Depends(get_current_user)):
    from app.mcp.server import tool_get_spending_insights
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, functools.partial(tool_get_spending_insights, user.id)
    )
    return result.get("insights", [])


@router.post("/reminders/trigger")
async def trigger_reminders(user: User = Depends(get_current_user)):
    return await reminder_service.trigger_now()