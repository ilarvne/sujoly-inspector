from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, JSON, Uuid
from datetime import datetime
import uuid

from agent.config.settings import settings

Base = declarative_base()


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column("metadata", JSON, nullable=True)


# Handle asyncpg SSL compatibility - asyncpg doesn't understand sslmode parameter
# Parse it out and convert to connect_args
_db_url = settings.database_url
_connect_args = {}
if "sslmode=disable" in _db_url:
    _db_url = _db_url.replace("?sslmode=disable", "").replace("&sslmode=disable", "")
    _connect_args["ssl"] = None

engine = create_async_engine(
    _db_url,
    echo=settings.debug,
    connect_args=_connect_args,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def init_db():
    """Create all tables registered on Base.metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
