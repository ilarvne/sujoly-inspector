"""SQLAlchemy async database infrastructure.

Provides:
- Base: declarative base for ORM models
- engine: async engine (asyncpg driver)
- async_session: session factory
- get_session: FastAPI dependency for async session injection

Schema management is via Alembic migrations (NOT Base.metadata.create_all).
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from api.config.settings import settings

Base = declarative_base()

# Handle asyncpg SSL compatibility — asyncpg doesn't understand sslmode parameter.
# Parse it out and convert to connect_args (Pitfall #4 from RESEARCH.md).
_db_url = settings.database_url
_connect_args: dict = {}
if "sslmode=disable" in _db_url:
    _db_url = _db_url.replace("? sslmode=disable", "").replace("&sslmode=disable", "")
    _db_url = _db_url.replace("?sslmode=disable", "").replace("&sslmode=disable", "")
    _connect_args["ssl"] = None

engine = create_async_engine(
    _db_url,
    echo=settings.debug,
    connect_args=_connect_args,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session() as session:
        yield session
