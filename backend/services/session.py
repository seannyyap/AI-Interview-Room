import json
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel
from redis.asyncio import Redis
from backend.config import settings


class SessionMetadata(BaseModel):
    id: str
    user_id: str
    started_at: datetime
    status: str = "active"
    client_ip: str
    interview_config: Optional[Dict] = None


class SessionManager:
    """Tracks active interview sessions in Redis."""
    def __init__(self):
        self._redis = Redis(
            host=settings.redis_host, 
            port=settings.redis_port, 
            decode_responses=True
        )

    async def create_session(self, session_id: str, user_id: str, client_ip: str) -> SessionMetadata:
        """Create a session record in Redis with a 1-hour TTL."""
        session = SessionMetadata(
            id=session_id,
            user_id=user_id,
            started_at=datetime.now(),
            client_ip=client_ip
        )
        
        await self._redis.setex(
            f"session:{session_id}",
            3600,  # 1 hour expiry
            session.model_dump_json()
        )
        return session

    async def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        data = await self._redis.get(f"session:{session_id}")
        if data:
            return SessionMetadata.model_validate_json(data)
        return None

    async def update_config(self, session_id: str, config: Dict):
        session = await self.get_session(session_id)
        if session:
            session.interview_config = config
            await self._redis.setex(
                f"session:{session_id}",
                3600,
                session.model_dump_json()
            )

    async def remove_session(self, session_id: str):
        await self._redis.delete(f"session:{session_id}")

    async def close(self):
        await self._redis.close()
