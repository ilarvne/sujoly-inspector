"""Security middleware for the API."""

import secrets
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import HTTP_401_UNAUTHORIZED

from agent.config.settings import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_security = HTTPBearer(auto_error=False)


def _is_valid_api_key(candidate: str, valid_keys: list[str]) -> bool:
    return any(secrets.compare_digest(candidate, valid_key) for valid_key in valid_keys)


@dataclass
class UserProfile:
    """User profile information."""

    user_id: str
    tenant_id: str
    role: str = "user"
    scopes: list[str] = field(default_factory=list)


def _resolve_request_api_key(
    api_key: str | None,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if api_key:
        return api_key

    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials

    return None


async def get_current_user(
    api_key: Annotated[str | None, Security(api_key_header)] = None,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_security),
    ] = None,
) -> UserProfile:
    configured_keys = settings.get_agent_api_keys()

    if not configured_keys:
        if settings.environment != "development":
            raise HTTPException(
                status_code=503,
                detail="Server misconfigured: no API keys set",
            )
        return UserProfile(user_id="dev-user", tenant_id="dev-tenant", role="admin")

    provided_key = _resolve_request_api_key(api_key=api_key, credentials=credentials)
    if not provided_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer, ApiKey"},
        )

    if _is_valid_api_key(provided_key, configured_keys):
        return UserProfile(
            user_id="default-user",
            tenant_id="default-tenant",
            role="user",
        )

    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )
