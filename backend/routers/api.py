"""
REST API endpoints — interview history and health check.
"""
from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.models.db_models import Interview
from backend.models.schemas import InterviewSummary, HealthStatus

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check(request: Request):
    """Enhanced health check — reports AI provider readiness."""
    stt_ready = getattr(request.app.state, "stt_provider", None) is not None and request.app.state.stt_provider.is_ready()
    llm_ready = getattr(request.app.state, "llm_provider", None) is not None and request.app.state.llm_provider.is_ready()
    tts_ready = getattr(request.app.state, "tts_provider", None) is not None and request.app.state.tts_provider.is_ready()

    all_ready = stt_ready and llm_ready and tts_ready

    return HealthStatus(
        status="ok" if all_ready else "degraded",
        version="0.4.0",
        ai_backend=settings.ai_backend,
        stt_ready=stt_ready,
        llm_ready=llm_ready,
        tts_ready=tts_ready,
    )


@router.get("/interviews", response_model=List[InterviewSummary])
async def list_interviews(
    db: AsyncSession = Depends(get_db),
):
    """List all interviews."""
    result = await db.execute(select(Interview).order_by(Interview.started_at.desc()))
    interviews = list(result.scalars().all())

    return [
        InterviewSummary(
            id=iv.id,
            position=iv.position,
            date=iv.started_at.strftime("%Y-%m-%d"),
            status=iv.status,
            duration_min=iv.duration_min,
        )
        for iv in interviews
    ]
