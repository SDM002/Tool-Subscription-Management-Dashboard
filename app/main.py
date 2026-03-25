"""
app/main.py
FastAPI application factory.
- Creates DB tables on startup
- Registers all routers under /api
- Starts the reminder scheduler
- Serves the static frontend
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_tables
import app.models  # noqa: F401 — registers all ORM models with SQLAlchemy

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("Starting %s …", settings.app_name)
    await create_tables()
    logger.info("Database tables ready.")

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


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Subscription dashboard with LangGraph + Groq + MCP agent",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all API routers
    from app.auth.routes import router as auth_router
    from app.routes.subscriptions import router as sub_router
    from app.routes.dashboard import router as dash_router
    from app.routes.chat import router as chat_router #
    from app.routes.health import router as health_router

    app.include_router(auth_router,   prefix="/api")
    app.include_router(sub_router,    prefix="/api")
    app.include_router(dash_router,   prefix="/api")
    app.include_router(chat_router,   prefix="/api")
    app.include_router(health_router, prefix="/api")

    # Serve static frontend at /
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
