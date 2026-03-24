"""
app/main.py  [NEW]

FastAPI application factory.
- Registers all routers
- Creates DB tables on startup
- Serves the static frontend
- Configures CORS for local development
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_tables

# Import all models so SQLAlchemy metadata is populated before create_tables()
import app.models  # noqa: F401

logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("Starting up %s …", settings.app_name)
    await create_tables()
    logger.info("Database tables ready.")

    # Start scheduler (phases 3+) — imported lazily to avoid circular imports
    try:
        from app.services.reminder_service import reminder_service
        reminder_service.start()
        logger.info("Reminder scheduler started.")
    except Exception as exc:
        logger.warning("Scheduler not started: %s", exc)

    yield

    # SHUTDOWN
    logger.info("Shutting down …")
    try:
        from app.services.reminder_service import reminder_service
        reminder_service.stop()
    except Exception:
        pass


# ── App instance ─────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Manage your software subscriptions with an AI assistant.",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── API Routers ───────────────────────────────────────────
    from app.auth.routes import router as auth_router
    from app.routes.subscriptions import router as sub_router
    from app.routes.health import router as health_router

    app.include_router(auth_router, prefix="/api")
    app.include_router(sub_router, prefix="/api")
    app.include_router(health_router, prefix="/api")

    # Phase 2 routers (dashboard + chat) — added after implementation
    try:
        from app.routes.dashboard import router as dashboard_router
        app.include_router(dashboard_router, prefix="/api")
    except ImportError:
        pass

    try:
        from app.routes.chat import router as chat_router
        app.include_router(chat_router, prefix="/api")
    except ImportError:
        pass

    # ── Static frontend ───────────────────────────────────────
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
