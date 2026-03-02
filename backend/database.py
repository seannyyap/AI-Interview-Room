"""
Async SQLAlchemy 2.0 database engine and session factory.
Uses asyncpg for PostgreSQL (standard) with aiosqlite as a local fallback.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.config import settings


def _build_db_url() -> str:
    """
    Build the async database URL for PostgreSQL.
    """
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    # Standard PostgreSQL connection using settings
    return (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )


db_url = _build_db_url()

engine = create_async_engine(
    db_url,
    echo=False,        # Set True for SQL debugging
    # Only set pool settings for PostgreSQL
    **({"pool_size": 5, "max_overflow": 10} if "postgresql" in db_url else {}),
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async database session."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
