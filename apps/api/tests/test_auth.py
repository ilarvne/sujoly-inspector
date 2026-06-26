"""Tests for JWT authentication and RBAC dependencies."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.dependencies.auth import require_role


class TestAuthEndpoints:
    """Tests for /api/v1/auth endpoints."""

    def test_token_with_username(self, test_client):
        """POST /api/v1/auth/token with username returns JWT."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.username = "admin"
        mock_user.role = "admin"
        mock_user.full_name = "Admin"
        with patch(
            "api.routes.auth.auth_service.get_user_by_username",
            AsyncMock(return_value=mock_user),
        ), patch(
            "api.routes.auth.auth_service.create_access_token",
            return_value="signed-token",
        ):
            response = test_client.post(
                "/api/v1/auth/token",
                json={"username": "admin"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "signed-token"
        assert data["token_type"] == "bearer"

    def test_token_with_api_key(self, test_client):
        """POST /api/v1/auth/token with api_key returns JWT."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.username = "admin"
        mock_user.role = "admin"
        mock_user.full_name = "Admin"
        with patch(
            "api.routes.auth.auth_service.get_user_by_api_key",
            AsyncMock(return_value=mock_user),
        ), patch(
            "api.routes.auth.auth_service.create_access_token",
            return_value="signed-token",
        ):
            response = test_client.post(
                "/api/v1/auth/token",
                json={"api_key": "test-key"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_token_invalid_user(self, test_client):
        """POST /api/v1/auth/token with unknown username returns 401."""
        with patch(
            "api.routes.auth.auth_service.get_user_by_username",
            AsyncMock(return_value=None),
        ), patch(
            "api.routes.auth.auth_service.get_user_by_api_key",
            AsyncMock(return_value=None),
        ):
            response = test_client.post(
                "/api/v1/auth/token",
                json={"username": "nonexistent"},
            )
        assert response.status_code == 401

    def test_me_with_valid_token(self, auth_client, mock_user):
        """GET /api/v1/auth/me with valid JWT returns user info."""
        response = auth_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == mock_user.username
        assert data["role"] == mock_user.role
        assert data["id"] == str(mock_user.id)

    def test_me_without_token(self, test_client):
        """GET /api/v1/auth/me without Authorization header returns 401."""
        response = test_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self, test_client):
        """GET /api/v1/auth/me with malformed JWT returns 401."""
        response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_require_role_inspector_allows_admin(self, mock_user):
        """require_role('inspector') allows admin role."""
        checker = require_role("inspector")
        result = checker(mock_user)
        assert result == mock_user

    def test_require_role_engineer_rejects_inspector(self, mock_inspector):
        """require_role('engineer') rejects inspector role → 403."""
        checker = require_role("engineer")
        with pytest.raises(HTTPException) as exc_info:
            checker(mock_inspector)
        assert exc_info.value.status_code == 403

    def test_require_role_admin_rejects_engineer(self, mock_engineer):
        """require_role('admin') rejects engineer role → 403."""
        checker = require_role("admin")
        with pytest.raises(HTTPException) as exc_info:
            checker(mock_engineer)
        assert exc_info.value.status_code == 403
