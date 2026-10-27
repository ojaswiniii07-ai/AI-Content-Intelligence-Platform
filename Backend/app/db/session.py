import asyncio
import time
from typing import AsyncGenerator, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import logger

# Configure async engine
connect_args = {}
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if "sqlite" in settings.async_database_url:
    connect_args["check_same_thread"] = False
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    if "postgresql" in settings.async_database_url:
        connect_args["timeout"] = 2

engine = create_async_engine(
    settings.async_database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an isolated async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_readiness() -> Tuple[bool, str, float]:
    """
    Actively checks if the database is reachable by executing a lightweight SELECT 1 query.
    Returns (is_ready, message_or_error, latency_ms).
    NEVER reports ready unless a real connection query succeeded.
    """
    start_time = time.perf_counter()
    try:
        async def _ping():
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_ping(), timeout=2.0)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return True, "Database connection operational", latency_ms
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        error_msg = str(exc)
        logger.warning(f"Database readiness check failed ({latency_ms}ms): {error_msg}")
        return False, error_msg, latency_ms
