"""FastAPI authentication and RBAC dependencies.

Provides:
- oauth2_scheme: OAuth2PasswordBearer for token extraction
- get_current_user: dependency that decodes JWT and loads user
- require_role: dependency factory for role-based access control
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from api.models.user import UserModel
from api.services import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    """FastAPI dependency: decode JWT and return the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth_service.decode_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = await auth_service.get_user_by_id(uuid.UUID(user_id))
    if user is None:
        raise credentials_exception
    return user


def require_role(required_role: str):
    """Dependency factory for role enforcement per D-12 permissions matrix.

    Role hierarchy: viewer < inspector < engineer < admin.
    Raises 403 if the current user's role is insufficient.
    """
    role_hierarchy = {"viewer": 0, "inspector": 1, "engineer": 2, "admin": 3}

    async def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if role_hierarchy.get(current_user.role, -1) < role_hierarchy.get(required_role, -1):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' insufficient. Requires '{required_role}' or higher.",
            )
        return current_user

    return role_checker
