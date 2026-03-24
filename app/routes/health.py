"""
app/routes/health.py  [NEW]
Health check + admin utilities.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0")


@router.post("/admin/reminders/trigger")
async def trigger_reminders(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Manually trigger the renewal reminder check (for testing)."""
    from app.services.reminder_service import reminder_service
    return await reminder_service.trigger_now()
