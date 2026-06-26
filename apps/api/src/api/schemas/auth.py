"""Pydantic schemas for authentication endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TokenRequest(BaseModel):
    """Request body for POST /api/v1/auth/token."""

    username: str | None = None
    api_key: str | None = None


class TokenResponse(BaseModel):
    """Response with JWT access token and token type."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response with authenticated user info."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    role: str
    full_name: str | None = None
    created_at: datetime
