"""app/routes/health.py — health check."""
from fastapi import APIRouter
router = APIRouter(tags=["Health"])

@router.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
