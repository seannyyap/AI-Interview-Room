"""
SessionManager — tracks active interview sessions in Redis.

Provides session creation, retrieval, config updating, and cleanup.
Handles Redis connection failures gracefully so they don't crash the
WebSocket endpoint.
"""
import logging
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel
from redis.asyncio import Redis
from backend.config import settings

logger = logging.getLogger("services.session")


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
        self._redis: Optional[Redis] = None

    def _get_redis(self) -> Redis:
        """Lazy Redis connection — created on first use, not at import time."""
        if self._redis is None:
            self._redis = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
        return self._redis

    async def create_session(self, session_id: str, user_id: str, client_ip: str) -> Optional[SessionMetadata]:
        """Create a session record in Redis with a 1-hour TTL."""
        session = SessionMetadata(
            id=session_id,
            user_id=user_id,
            started_at=datetime.now(),
            client_ip=client_ip
        )
        try:
            await self._get_redis().setex(
                f"session:{session_id}",
                3600,  # 1 hour expiry
                session.model_dump_json()
            )
            return session
        except Exception as e:
            logger.warning(f"Failed to create session in Redis (non-fatal): {e}")
            return session  # Return the session anyway, it just won't be in Redis

    async def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        try:
            data = await self._get_redis().get(f"session:{session_id}")
            if data:
                return SessionMetadata.model_validate_json(data)
        except Exception as e:
            logger.warning(f"Failed to get session from Redis: {e}")
        return None

    async def update_config(self, session_id: str, config: Dict):
        try:
            session = await self.get_session(session_id)
            if session:
                session.interview_config = config
                await self._get_redis().setex(
                    f"session:{session_id}",
                    3600,
                    session.model_dump_json()
                )
        except Exception as e:
            logger.warning(f"Failed to update session config in Redis: {e}")

    async def remove_session(self, session_id: str):
        try:
            await self._get_redis().delete(f"session:{session_id}")
        except Exception as e:
            logger.warning(f"Failed to remove session from Redis: {e}")

    async def close(self):
        if self._redis:
            try:
                await self._redis.close()
            except Exception as e:
                logger.warning(f"Failed to close Redis connection: {e}")
            self._redis = None
