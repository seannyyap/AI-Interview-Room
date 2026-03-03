"""
Shared test fixtures for the AI Interview Room backend.

Sets up a mock-based FastAPI test client that uses in-memory SQLite
instead of PostgreSQL, and Mock AI providers instead of real models.
"""
import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.models.db_models import Base
from backend.providers.mock import MockSTTProvider, MockLLMProvider, MockTTSProvider

# ── In-memory SQLite engine for tests ─────────────────────────
_test_engine = create_async_engine("sqlite+aiosqlite:///", echo=False)

_TestSessionFactory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Monkey-patch database BEFORE importing routers ────────────
import backend.database as db_module

db_module.AsyncSessionFactory = _TestSessionFactory


async def _test_get_db():
    async with _TestSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


db_module.get_db = _test_get_db


# ── Mock SessionManager to avoid Redis dependency ─────────────
class MockSessionManager:
    """In-memory session manager for tests — no Redis needed."""
    def __init__(self):
        self._sessions = {}

    async def create_session(self, session_id, user_id, client_ip):
        self._sessions[session_id] = {"user_id": user_id, "client_ip": client_ip}
        return MagicMock(id=session_id)

    async def get_session(self, session_id):
        return self._sessions.get(session_id)

    async def update_config(self, session_id, config):
        if session_id in self._sessions:
            self._sessions[session_id]["config"] = config

    async def remove_session(self, session_id):
        self._sessions.pop(session_id, None)

    async def close(self):
        self._sessions.clear()


# Monkey-patch the session manager in ws module
import backend.routers.ws as ws_module
ws_module.session_manager = MockSessionManager()


# ── Test app factory ──────────────────────────────────────────
def _create_test_app() -> FastAPI:
    """Create a FastAPI app wired with mock providers and test DB."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Create tables in test DB
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Load mock providers
        stt = MockSTTProvider()
        llm = MockLLMProvider()
        tts = MockTTSProvider()
        await stt.load()
        await llm.load()
        await tts.load()

        app.state.stt_provider = stt
        app.state.llm_provider = llm
        app.state.tts_provider = tts

        yield

        await stt.unload()
        await llm.unload()
        await tts.unload()

    from backend.routers import api, ws

    test_app = FastAPI(lifespan=lifespan)
    test_app.include_router(api.router, prefix="/api")
    test_app.include_router(ws.router)

    return test_app


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_app():
    return _create_test_app()


@pytest.fixture(scope="session")
def client(test_app):
    with TestClient(test_app) as c:
        yield c
