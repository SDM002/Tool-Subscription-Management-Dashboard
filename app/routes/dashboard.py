"""
app/routes/dashboard.py  [NEW]

Dashboard endpoints:
  GET /api/dashboard/summary   → spending totals + renewals
  GET /api/dashboard/renewals  → upcoming renewals (configurable window)
  GET /api/dashboard/insights  → AI-free cost-saving insights
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse, RenewalItem
from app.services.dashboard_service import dashboard_service
from app.services.pricing_service import pricing_service, InsightItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummaryResponse:
    """
    Full dashboard summary:
    total spend, upcoming renewals (7-day + 30-day), breakdown by category.
    """
    return await dashboard_service.get_summary(db, current_user.id)


@router.get("/renewals", response_model=list[RenewalItem])
async def get_upcoming_renewals(
    days: int = Query(30, ge=1, le=365, description="Look-ahead window in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RenewalItem]:
    """Return subscriptions renewing within the next N days."""
    return await dashboard_service.get_upcoming_renewals(db, current_user.id, days)


@router.get("/insights")
async def get_spending_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InsightItem]:
    """
    Rule-based spending insights:
    duplicates, annual-billing savings, high-cost tools.
    """
    return await pricing_service.get_insights(db, current_user.id)
