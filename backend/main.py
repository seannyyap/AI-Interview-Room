"""
AI Interview Room — FastAPI Backend
Main entry point for the FastAPI application.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import api, ws

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backend")

app = FastAPI(
    title="AI Interview Room",
    version="0.1.0",
    description="AI-powered mock interview platform",
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


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting AI Interview Room Backend")
    logger.info(f"AI Backend Mode: {settings.ai_backend}")
    logger.info(f"CORS Origins: {origins}")


@app.get("/")
async def root():
    return {
        "message": "AI Interview Room Backend is running",
        "docs": "/docs",
        "health": "/api/health"
    }
