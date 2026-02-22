from datetime import datetime
from uuid import uuid4
from typing import Dict, Optional
from pydantic import BaseModel, Field


class SessionMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"
    client_ip: str
    interview_config: Optional[Dict] = None


class SessionManager:
    """Tracks active interview sessions in-memory."""
    def __init__(self):
        self._sessions: Dict[str, SessionMetadata] = {}

    def create_session(self, client_ip: str) -> SessionMetadata:
        session = SessionMetadata(client_ip=client_ip)
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        return self._sessions.get(session_id)

    def update_config(self, session_id: str, config: Dict):
        if session_id in self._sessions:
            self._sessions[session_id].interview_config = config

    def remove_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    @property
    def active_count(self) -> int:
        return len(self._sessions)
