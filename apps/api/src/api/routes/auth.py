"""Authentication endpoints for the SuJoly Inspector API.

Provides:
- POST /api/v1/auth/token: JWT token issuance via username or API key (D-11)
- GET /api/v1/auth/me: Current authenticated user info (D-11)
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.auth import get_current_user
from api.models.user import UserModel
from api.schemas.auth import TokenRequest, TokenResponse, UserResponse
from api.services import auth_service

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post("/auth/token", response_model=TokenResponse)
async def token_endpoint(body: TokenRequest) -> TokenResponse:
    """Issue a JWT token given a username or API key (D-11).

    Accepts either `username` or `api_key` in the request body.
    Returns a signed JWT with user_id, username, role, and exp claims.
    Raises 401 if no matching user is found.
    """
    user = None

    if body.username:
        user = await auth_service.get_user_by_username(body.username)
    elif body.api_key:
        user = await auth_service.get_user_by_api_key(body.api_key)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )

    return TokenResponse(access_token=access_token)


@router.get("/auth/me", response_model=UserResponse)
async def me_endpoint(
    current_user: UserModel = Depends(get_current_user),
) -> UserResponse:
    """Return the currently authenticated user's info (D-11).

    Requires a valid JWT in the Authorization header.
    """
    return UserResponse.model_validate(current_user)
