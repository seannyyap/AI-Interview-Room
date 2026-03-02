"""
Interview repository — CRUD operations for interviews and messages tables.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.db_models import Interview, Message


class InterviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_interview(self, user_id: str = "anonymous", position: str = "Software Engineer", config: dict = None) -> Interview:
        """Create a new interview record."""
        interview = Interview(user_id=user_id, position=position, config=config)
        self.db.add(interview)
        await self.db.flush()
        return interview

    async def get_by_id(self, interview_id: str) -> Interview | None:
        result = await self.db.execute(select(Interview).where(Interview.id == interview_id))
        return result.scalar_one_or_none()

    async def get_all_interviews(self) -> List[Interview]:
        """Get all interviews, ordered by most recent first."""
        result = await self.db.execute(
            select(Interview)
            .order_by(Interview.started_at.desc())
        )
        return list(result.scalars().all())

    async def end_interview(self, interview_id: str) -> None:
        """Mark an interview as completed."""
        await self.db.execute(
            update(Interview)
            .where(Interview.id == interview_id)
            .values(status="completed", ended_at=datetime.now(timezone.utc))
        )

    async def save_message(self, interview_id: str, role: str, content: str) -> Message:
        """Save a transcript or AI response message."""
        msg = Message(interview_id=interview_id, role=role, content=content)
        self.db.add(msg)
        await self.db.flush()
        return msg
