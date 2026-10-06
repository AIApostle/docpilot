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

from src.client.config import settings
from src.client.supabase_client import close_supabase_client
from src.pages.auth import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("docpilot.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and graceful shutdown lifecycle."""
    logger.info("Starting DocPilot API backend in %s mode...", settings.ENVIRONMENT)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
