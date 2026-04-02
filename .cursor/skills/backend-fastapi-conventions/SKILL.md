---
name: backend-fastapi-conventions
description: FastAPI backend with async SQLAlchemy, Pydantic schemas (camelCase aliases), app.state providers, and lifespan loading. Use when adding routes, changing config, or touching the database layer.
---

# Backend FastAPI Conventions

## Config

- Single source: `backend.config.settings` (Pydantic `BaseSettings`, env vars, optional `.env`).
- No hardcoded secrets; use `settings.postgres_host`, `settings.groq_api_key`, etc.

## Schemas & JSON

- All API/WS schemas live in `backend.models.schemas`.
- Use `BaseSchema` with `to_camel` alias generator; for JSON out use `model_dump(by_alias=True)` so the frontend gets camelCase (`isFinal`, `isComplete`, etc.).

## Database

- Async only: `AsyncSessionFactory` from `backend.database`; use `async with AsyncSessionFactory() as db:`.
- Repositories in `backend.repositories.*` (e.g. `InterviewRepository`) encapsulate persistence.
- Migrations: Alembic; run new migrations after schema changes. Do not create tables manually in production.

## Lifespan & Providers

- AI providers (STT, LLM, TTS) are loaded in `main.py` lifespan; stored on `app.state` as `stt_provider`, `llm_provider`, `tts_provider`.
- Routers receive `websocket.app.state.llm_provider` etc.; never instantiate providers inside request handlers.

## Logging

- Use module logger: `logger = logging.getLogger(__name__)` or `logging.getLogger("ws")` in `ws.py`.
- Log errors with `exc_info=True` where appropriate.

## Structure

- Routers: `backend.routers` (e.g. `api`, `ws`); include with `app.include_router(router, prefix=..., tags=...)`.
- Business logic in `backend.services.*`; data access in `backend.repositories.*`; providers in `backend.providers.*`.
