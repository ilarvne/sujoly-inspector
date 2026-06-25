import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from agent.config.settings import settings
from agent.server_auth import get_current_user


@pytest.fixture(autouse=True)
def reset_agent_api_keys(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "agent_api_key", None)
    monkeypatch.setattr(settings, "agent_api_keys", "")


@pytest.mark.asyncio
async def test_get_current_user_dev_mode_without_keys():
    user = await get_current_user(api_key=None, credentials=None)
    assert user.user_id == "dev-user"
    assert user.role == "admin"


@pytest.mark.asyncio
async def test_get_current_user_accepts_x_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "agent_api_key", "primary-key")

    user = await get_current_user(api_key="primary-key", credentials=None)

    assert user.user_id == "default-user"
    assert user.role == "user"


@pytest.mark.asyncio
async def test_get_current_user_accepts_bearer_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "agent_api_key", "primary-key")

    user = await get_current_user(
        api_key=None,
        credentials=HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="primary-key",
        ),
    )

    assert user.user_id == "default-user"


@pytest.mark.asyncio
async def test_get_current_user_accepts_rotated_keys(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "agent_api_key", "primary-key")
    monkeypatch.setattr(settings, "agent_api_keys", "secondary-key, tertiary-key")

    user = await get_current_user(api_key="tertiary-key", credentials=None)

    assert user.user_id == "default-user"


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_credentials(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "agent_api_key", "primary-key")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(api_key=None, credentials=None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing authentication credentials"


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_credentials(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "agent_api_key", "primary-key")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(api_key="wrong-key", credentials=None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"
