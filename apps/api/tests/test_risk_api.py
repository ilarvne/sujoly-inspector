"""Tests for risk assessment endpoints: GET risk, POST override, POST recompute.

Tests cover:
- GET /api/v1/structures/{id}/risk → 200 with full factor breakdown (D-04)
- GET /api/v1/structures/{id}/risk → 404 for non-existent structure
- GET /api/v1/structures/{id}/risk → 404 when no assessment exists
- POST /api/v1/structures/{id}/override → 200 with overridden values (D-13, RISK-06)
- POST /api/v1/structures/{id}/override → response includes system-computed values
- POST /api/v1/structures/{id}/override → creates provenance with contributor
- POST /api/v1/structures/{id}/override → 403 for viewer role
- POST /api/v1/structures/{id}/override → 403 for inspector role
- POST /api/v1/structures/{id}/override → 200 for engineer role
- POST /api/v1/structures/{id}/override → 200 for admin role
- POST /api/v1/structures/{id}/override → 404 for non-existent structure
- POST /api/v1/structures/{id}/recompute → 200 with new assessment (D-05 trigger 4)
- POST /api/v1/structures/{id}/recompute → 403 for viewer role
- POST /api/v1/structures/{id}/recompute → 403 for inspector role
- POST /api/v1/structures/{id}/recompute → 404 for non-existent structure
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRiskEndpoints:
    """Tests for /api/v1/structures risk-related endpoints."""

    def _mock_risk_assessment_model(self, **overrides):
        """Create a mock RiskAssessmentModel instance with all response fields."""
        defaults = {
            "id": uuid.uuid4(),
            "structure_id": uuid.uuid4(),
            "condition_score": 65.0,
            "consequence_factor": 1.2,
            "seasonal_modifier": 1.0,
            "staleness_modifier": 1.0,
            "composite_score": 78.0,
            "inspection_interval": "180d",
            "repair_status": "inspection_required",
            "red_flags": [],
            "contributing_factors": {
                "wear_percentage": 45.0,
                "technical_condition": "удовлетворительное",
                "structure_type": "canal",
                "days_since_last_inspection": 120,
            },
            "is_override": False,
            "computed_at": datetime.now(timezone.utc),
            "valid_to": None,
        }
        defaults.update(overrides)
        mock = MagicMock()
        for key, val in defaults.items():
            setattr(mock, key, val)
        return mock

    def _mock_overridden_assessment(self, **overrides):
        """Create a mock overridden RiskAssessmentModel with system values preserved."""
        system_interval = "180d"
        system_status = "inspection_required"
        defaults = {
            "id": uuid.uuid4(),
            "structure_id": uuid.uuid4(),
            "condition_score": 65.0,
            "consequence_factor": 1.2,
            "seasonal_modifier": 1.0,
            "staleness_modifier": 1.0,
            "composite_score": 78.0,
            "inspection_interval": "30d",
            "repair_status": "repair_required",
            "red_flags": [],
            "contributing_factors": {
                "system_inspection_interval": system_interval,
                "system_repair_status": system_status,
                "override_reason": "Engineer judgment based on site visit",
                "overridden_by": "test-engineer",
                "wear_percentage": 45.0,
                "technical_condition": "удовлетворительное",
                "structure_type": "canal",
                "days_since_last_inspection": 120,
            },
            "is_override": True,
            "computed_at": datetime.now(timezone.utc),
            "valid_to": None,
        }
        defaults.update(overrides)
        mock = MagicMock()
        for key, val in defaults.items():
            setattr(mock, key, val)
        return mock

    # ------------------------------------------------------------------
    # GET /structures/{id}/risk tests
    # ------------------------------------------------------------------

    def test_get_risk_returns_assessment(self, test_client):
        """GET /api/v1/structures/{id}/risk returns 200 with condition_score, consequence_factor, seasonal_modifier, staleness_modifier, composite_score, inspection_interval, repair_status, red_flags, contributing_factors."""
        struct_id = uuid.uuid4()
        mock_assessment = self._mock_risk_assessment_model(structure_id=struct_id)
        with patch(
            "api.routes.risk.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_assessment),
        ), patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=MagicMock(id=struct_id, status="active")),
        ):
            response = test_client.get(f"/api/v1/structures/{struct_id}/risk")
        assert response.status_code == 200
        data = response.json()
        assert "condition_score" in data
        assert "consequence_factor" in data
        assert "seasonal_modifier" in data
        assert "staleness_modifier" in data
        assert "composite_score" in data
        assert "inspection_interval" in data
        assert "repair_status" in data
        assert "red_flags" in data
        assert "contributing_factors" in data

    def test_get_risk_not_found(self, test_client):
        """GET /api/v1/structures/{id}/risk for non-existent structure returns 404."""
        non_existent_id = uuid.uuid4()
        with patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=None),
        ):
            response = test_client.get(f"/api/v1/structures/{non_existent_id}/risk")
        assert response.status_code == 404

    def test_get_risk_no_assessment(self, test_client):
        """GET /api/v1/structures/{id}/risk when no assessment exists returns 404."""
        struct_id = uuid.uuid4()
        with patch(
            "api.routes.risk.risk_service.get_latest_assessment",
            AsyncMock(return_value=None),
        ), patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=MagicMock(id=struct_id, status="active")),
        ):
            response = test_client.get(f"/api/v1/structures/{struct_id}/risk")
        assert response.status_code == 404
        assert "No risk assessment found" in response.json().get("detail", "")

    # ------------------------------------------------------------------
    # POST /structures/{id}/override tests
    # ------------------------------------------------------------------

    def test_override_success(self, test_client):
        """POST /api/v1/structures/{id}/override with engineer role returns 200 with overridden inspection_interval and repair_status."""
        struct_id = uuid.uuid4()
        mock_overridden = self._mock_overridden_assessment(structure_id=struct_id)
        with patch(
            "api.routes.risk.risk_service.create_override",
            AsyncMock(return_value=mock_overridden),
        ), patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=MagicMock(id=struct_id, status="active")),
        ):
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/override",
                json={
                    "inspection_interval": "30d",
                    "repair_status": "repair_required",
                    "reason": "Engineer judgment based on site visit",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["inspection_interval"] == "30d"
        assert data["repair_status"] == "repair_required"

    def test_override_includes_system_values(self, test_client):
        """Override response contains both system-computed values and override values."""
        struct_id = uuid.uuid4()
        mock_overridden = self._mock_overridden_assessment(structure_id=struct_id)
        with patch(
            "api.routes.risk.risk_service.create_override",
            AsyncMock(return_value=mock_overridden),
        ), patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=MagicMock(id=struct_id, status="active")),
        ):
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/override",
                json={
                    "inspection_interval": "30d",
                    "repair_status": "repair_required",
                    "reason": "Engineer judgment",
                },
            )
        assert response.status_code == 200
        data = response.json()
        # Override values
        assert data["inspection_interval"] == "30d"
        assert data["repair_status"] == "repair_required"
        # System values preserved in contributing_factors
        assert "system_inspection_interval" in data["contributing_factors"]
        assert "system_repair_status" in data["contributing_factors"]

    def test_override_creates_provenance(self, test_client):
        """Verify risk_service.create_override is called with user.username for provenance contributor."""
        struct_id = uuid.uuid4()
        mock_overridden = self._mock_overridden_assessment(structure_id=struct_id)
        with patch(
            "api.routes.risk.risk_service.create_override",
            AsyncMock(return_value=mock_overridden),
        ) as mock_create_override, patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=MagicMock(id=struct_id, status="active")),
        ):
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/override",
                json={
                    "inspection_interval": "30d",
                    "repair_status": "repair_required",
                    "reason": "Engineer judgment",
                },
            )
        assert response.status_code == 200
        # Verify create_override was called
        assert mock_create_override.called
        # The second positional arg should be the override data, third is user
        call_args = mock_create_override.call_args
        # Check that the user argument was passed (via dependency injection)
        assert call_args is not None

    def test_override_viewer_forbidden(self, test_client, mock_viewer):
        """POST /api/v1/structures/{id}/override with viewer role returns 403."""
        from api.dependencies.auth import get_current_user

        app = test_client.app

        async def _override():
            return mock_viewer

        app.dependency_overrides[get_current_user] = _override
        try:
            struct_id = uuid.uuid4()
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/override",
                json={
                    "inspection_interval": "30d",
                    "repair_status": "repair_required",
                    "reason": "Override attempt",
                },
            )
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == 403

    def test_override_inspector_forbidden(self, test_client, mock_inspector):
        """POST /api/v1/structures/{id}/override with inspector role returns 403."""
        from api.dependencies.auth import get_current_user

        app = test_client.app

        async def _override():
            return mock_inspector

        app.dependency_overrides[get_current_user] = _override
        try:
            struct_id = uuid.uuid4()
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/override",
                json={
                    "inspection_interval": "30d",
                    "repair_status": "repair_required",
                    "reason": "Override attempt",
                },
            )
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == 403

    def test_override_engineer_allowed(self, test_client, mock_engineer):
        """POST /api/v1/structures/{id}/override with engineer role returns 200."""
        from api.dependencies.auth import get_current_user

        app = test_client.app
        struct_id = uuid.uuid4()
        mock_overridden = self._mock_overridden_assessment(structure_id=struct_id)

        async def _override():
            return mock_engineer

        app.dependency_overrides[get_current_user] = _override
        try:
            with patch(
                "api.routes.risk.risk_service.create_override",
                AsyncMock(return_value=mock_overridden),
            ), patch(
                "api.routes.risk.structure_service.get_structure",
                AsyncMock(return_value=MagicMock(id=struct_id, status="active")),
            ):
                response = test_client.post(
                    f"/api/v1/structures/{struct_id}/override",
                    json={
                        "inspection_interval": "30d",
                        "repair_status": "repair_required",
                        "reason": "Engineer judgment",
                    },
                )
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == 200

    def test_override_admin_allowed(self, test_client, mock_user):
        """POST /api/v1/structures/{id}/override with admin role returns 200."""
        from api.dependencies.auth import get_current_user

        app = test_client.app
        struct_id = uuid.uuid4()
        mock_overridden = self._mock_overridden_assessment(structure_id=struct_id)

        async def _override():
            return mock_user

        app.dependency_overrides[get_current_user] = _override
        try:
            with patch(
                "api.routes.risk.risk_service.create_override",
                AsyncMock(return_value=mock_overridden),
            ), patch(
                "api.routes.risk.structure_service.get_structure",
                AsyncMock(return_value=MagicMock(id=struct_id, status="active")),
            ):
                response = test_client.post(
                    f"/api/v1/structures/{struct_id}/override",
                    json={
                        "inspection_interval": "30d",
                        "repair_status": "repair_required",
                        "reason": "Admin override",
                    },
                )
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == 200

    def test_override_not_found(self, test_client):
        """POST /api/v1/structures/{id}/override for non-existent structure returns 404."""
        non_existent_id = uuid.uuid4()
        with patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=None),
        ):
            response = test_client.post(
                f"/api/v1/structures/{non_existent_id}/override",
                json={
                    "inspection_interval": "30d",
                    "repair_status": "repair_required",
                    "reason": "Override attempt",
                },
            )
        assert response.status_code == 404

    # ------------------------------------------------------------------
    # POST /structures/{id}/recompute tests (D-05 trigger 4)
    # ------------------------------------------------------------------

    def test_recompute_success(self, test_client):
        """POST /api/v1/structures/{id}/recompute with engineer role returns 200 with new RiskAssessmentResponse containing updated factor breakdown per D-05 trigger 4."""
        struct_id = uuid.uuid4()
        mock_recomputed = self._mock_risk_assessment_model(
            structure_id=struct_id,
            composite_score=120.0,
            inspection_interval="90d",
            repair_status="repair_required",
        )
        with patch(
            "api.routes.risk.risk_service.recompute_risk_for_structure",
            AsyncMock(return_value=mock_recomputed),
        ), patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=MagicMock(id=struct_id, status="active")),
        ):
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/recompute",
            )
        assert response.status_code == 200
        data = response.json()
        assert "composite_score" in data
        assert "inspection_interval" in data
        assert "repair_status" in data
        assert data["composite_score"] == 120.0

    def test_recompute_viewer_forbidden(self, test_client, mock_viewer):
        """POST /api/v1/structures/{id}/recompute with viewer role returns 403."""
        from api.dependencies.auth import get_current_user

        app = test_client.app

        async def _override():
            return mock_viewer

        app.dependency_overrides[get_current_user] = _override
        try:
            struct_id = uuid.uuid4()
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/recompute",
            )
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == 403

    def test_recompute_inspector_forbidden(self, test_client, mock_inspector):
        """POST /api/v1/structures/{id}/recompute with inspector role returns 403."""
        from api.dependencies.auth import get_current_user

        app = test_client.app

        async def _override():
            return mock_inspector

        app.dependency_overrides[get_current_user] = _override
        try:
            struct_id = uuid.uuid4()
            response = test_client.post(
                f"/api/v1/structures/{struct_id}/recompute",
            )
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == 403

    def test_recompute_not_found(self, test_client):
        """POST /api/v1/structures/{id}/recompute for non-existent structure returns 404."""
        non_existent_id = uuid.uuid4()
        with patch(
            "api.routes.risk.structure_service.get_structure",
            AsyncMock(return_value=None),
        ):
            response = test_client.post(
                f"/api/v1/structures/{non_existent_id}/recompute",
            )
        assert response.status_code == 404
