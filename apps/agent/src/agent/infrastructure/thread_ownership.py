"""Thread ownership tracking for access control."""

import structlog
from sqlalchemy import Column, String, DateTime, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.infrastructure.database import Base, async_session

logger = structlog.get_logger(__name__)


class ThreadOwnership(Base):
    __tablename__ = "thread_ownership"

    thread_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def ensure_thread_ownership(thread_id: str, user_id: str) -> None:
    """Record thread ownership on first use. Idempotent. Fire-and-forget safe."""
    try:
        async with async_session() as session:
            async with session.begin():
                existing = await session.execute(
                    select(ThreadOwnership).where(
                        ThreadOwnership.thread_id == thread_id
                    )
                )
                if not existing.scalar_one_or_none():
                    session.add(
                        ThreadOwnership(thread_id=thread_id, user_id=user_id)
                    )
    except Exception:
        logger.warning(
            "thread_ownership_record_failed",
            thread_id=thread_id,
            user_id=user_id,
            exc_info=True,
        )


async def check_thread_access(thread_id: str, user_id: str) -> bool:
    """Check if user owns the thread. Returns True if no ownership record (legacy threads)."""
    async with async_session() as session:
        result = await session.execute(
            select(ThreadOwnership).where(
                ThreadOwnership.thread_id == thread_id
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return True  # Legacy thread with no ownership record
        return record.user_id == user_id
