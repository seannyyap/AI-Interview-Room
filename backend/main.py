"""
AI Interview Room — FastAPI Backend
Main entry point for the FastAPI application.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import api, ws
from backend.database import engine
from backend.models.db_models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — create DB tables on startup, cleanup on shutdown."""
    logger.info(f"Starting AI Interview Room Backend")
    logger.info(f"AI Backend Mode: {settings.ai_backend}")

    # Create all tables (dev convenience — use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

    yield

    # Cleanup
    await engine.dispose()
    logger.info("Database engine disposed")


app = FastAPI(
    title="AI Interview Room",
    version="0.2.0",
    description="AI-powered mock interview platform",
    lifespan=lifespan,
)

# CORS — configured from environment
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(api.router, prefix="/api", tags=["API"])
app.include_router(ws.router, tags=["WebSocket"])


@app.get("/")
async def root():
    return {
        "message": "AI Interview Room Backend is running",
        "docs": "/docs",
        "health": "/api/health"
    }
