"""Authentication service — JWT encode/decode and user lookups."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select

from api.config.settings import settings
from api.infrastructure.database import async_session
from api.models.user import UserModel

ALGORITHM = "HS256"


def create_access_token(user_id: str, username: str, role: str) -> str:
    """Create a JWT token with user_id, username, role, and expiry."""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token with explicit HS256 algorithm."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


async def get_user_by_username(username: str) -> UserModel | None:
    """Lookup a user by username."""
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalar_one_or_none()


async def get_user_by_id(user_id: uuid.UUID) -> UserModel | None:
    """Lookup a user by UUID."""
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()


async def get_user_by_api_key(api_key: str) -> UserModel | None:
    """Lookup a user by API key."""
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.api_key == api_key)
        )
        return result.scalar_one_or_none()
