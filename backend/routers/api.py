from fastapi import APIRouter
from backend.models.schemas import InterviewSummary, InterviewDetail, TranscriptMessage, AIResponseMessage

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

@router.get("/interviews", response_model=list[InterviewSummary])
async def list_interviews():
    # Mock data for Phase 2
    return [
        InterviewSummary(
            id="1",
            position="Senior Software Engineer",
            date="2024-02-20",
            status="completed",
            duration_min=45
        ),
        InterviewSummary(
            id="2",
            position="System Architect",
            date="2024-02-21",
            status="completed",
            duration_min=30
        )
    ]

@router.get("/interviews/{interview_id}", response_model=InterviewDetail)
async def get_interview(interview_id: str):
    # Mock data for Phase 2
    return InterviewDetail(
        id=interview_id,
        position="Senior Software Engineer",
        date="2024-02-20",
        status="completed",
        duration_min=45,
        transcript=[
            AIResponseMessage(text="Hello! How are you today?", is_complete=True, timestamp="10:00 AM"),
            TranscriptMessage(text="I'm doing well, ready to start!", is_final=True, timestamp="10:01 AM"),
        ]
    )
