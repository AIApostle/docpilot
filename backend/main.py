import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure src/ is on sys.path so modules import relative to src/
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from client.config import settings
from client.supabase_client import close_supabase_client
from client.telegram import configure_telegram_webhook
from db.schema import verify_database_schema
from pages.auth import router as auth_router
from pages.chat import router as chat_router
from pages.memory import router as memory_router
from pages.telegram import router as telegram_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("docpilot.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and graceful shutdown lifecycle."""
    logger.info("Starting DocPilot API backend in %s mode...", settings.ENVIRONMENT)
    await verify_database_schema()
    if settings.ENVIRONMENT.lower() in {"production", "prod"}:
        await configure_telegram_webhook()
    yield
    logger.info("Shutting down DocPilot API backend, cleaning up resources...")
    await close_supabase_client()


app = FastAPI(
    title="DocPilot API",
    version="2.0.0",
    description="DocPilot: Agentic, memory-first clinical assistant for physicians.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Health & Readiness Check
@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Health check probe",
    description="Probing endpoint for uptime checks, monitoring, and Render zero-downtime deployments.",
)
async def health_check():
    return {
        "status": "ok",
        "app": "docpilot",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
    }


# Root Welcome & Status
@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Root service status",
)
async def root():
    return {
        "name": "DocPilot API",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs",
    }


# Mount Routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/chat", tags=["Consultations"])
app.include_router(chat_router, prefix="/chats", tags=["Consultations (Frontend Alias)"], include_in_schema=False)
app.include_router(memory_router, prefix="/memory", tags=["Memory Settings"])
app.include_router(telegram_router, prefix="/telegram", tags=["Telegram Bot"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
