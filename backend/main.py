"""
AI Interview Room — FastAPI Backend
Main entry point for the FastAPI application.

Phase 4: Loads real AI providers at startup via the lifespan context manager.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import api, ws
from backend.database import engine
from backend.models.db_models import Base
from backend.providers import get_all_providers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan — load AI models on startup, cleanup on shutdown.

    All three providers (STT, LLM, TTS) are instantiated and loaded here,
    then stored on app.state for access by routers.
    """
    logger.info("Starting AI Interview Room Backend")
    logger.info(f"AI Backend Mode: {settings.ai_backend}")

    # Create all tables (dev convenience — use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

    # ── Load AI Providers ────────────────────────────────────
    stt, llm, tts = get_all_providers()

    # Load each provider independently — one failure shouldn't prevent others
    for name, provider in [("STT", stt), ("LLM", llm), ("TTS", tts)]:
        try:
            logger.info(f"Loading {name} provider...")
            await provider.load()
        except Exception as e:
            logger.error(f"Failed to load {name} provider: {e}", exc_info=True)
            logger.warning(f"{name} features will be unavailable")

    # Store on app.state for router access
    app.state.stt_provider = stt
    app.state.llm_provider = llm
    app.state.tts_provider = tts

    logger.info(
        f"AI providers ready — STT: {stt.is_ready()}, "
        f"LLM: {llm.is_ready()}, TTS: {tts.is_ready()}"
    )

    yield

    # ── Cleanup ──────────────────────────────────────────────
    logger.info("Shutting down — unloading AI providers...")
    for name, provider in [("STT", stt), ("LLM", llm), ("TTS", tts)]:
        try:
            await provider.unload()
        except Exception as e:
            logger.error(f"Failed to unload {name}: {e}")

    # Close the session manager's Redis connection
    try:
        await ws.session_manager.close()
    except Exception as e:
        logger.warning(f"Failed to close session manager: {e}")

    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title="AI Interview Room",
    version="0.4.0",
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
