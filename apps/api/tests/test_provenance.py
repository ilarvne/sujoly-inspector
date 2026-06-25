"""Tests for provenance CRUD endpoints and provenance FK enforcement.

Tests cover:
- POST /api/v1/provenance → 201 with full record
- GET /api/v1/provenance/{id} → 200 with record
- GET /api/v1/provenance/{id} → 404 for non-existent
- GET /api/v1/provenance?source_type=... → filtered list
- GET /api/v1/provenance?confidence_level=... → filtered list
- test_fact_has_provenance → IntegrityError on missing provenance_id (DATA-07)
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestProvenanceEndpoints:
    """Tests for /api/v1/provenance CRUD endpoints."""

    def _mock_provenance(self, **overrides):
        """Create a mock ProvenanceModel instance."""
        defaults = {
            "id": uuid.uuid4(),
            "source_type": "kazvodhoz_spreadsheet",
            "source_reference": None,
            "confidence_level": "HIGH",
            "contributor": "ingest_pipeline",
            "recorded_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        mock = MagicMock()
        for key, val in defaults.items():
            setattr(mock, key, val)
        return mock

    def test_create_provenance(self, test_client):
        """POST /api/v1/provenance returns 201 with id, source_type, confidence_level, contributor, recorded_at."""
        mock_prov = self._mock_provenance()
        with patch(
            "api.routes.provenance.create_provenance",
            AsyncMock(return_value=mock_prov),
        ):
            response = test_client.post(
                "/api/v1/provenance",
                json={
                    "source_type": "kazvodhoz_spreadsheet",
                    "confidence_level": "HIGH",
                    "contributor": "ingest_pipeline",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["source_type"] == "kazvodhoz_spreadsheet"
        assert data["confidence_level"] == "HIGH"
        assert data["contributor"] == "ingest_pipeline"
        assert "recorded_at" in data

    def test_get_provenance_by_id(self, test_client):
        """GET /api/v1/provenance/{id} returns 200 with full record."""
        prov_id = uuid.uuid4()
        mock_prov = self._mock_provenance(id=prov_id)
        with patch(
            "api.routes.provenance.get_provenance",
            AsyncMock(return_value=mock_prov),
        ):
            response = test_client.get(f"/api/v1/provenance/{prov_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(prov_id)
        assert data["source_type"] == "kazvodhoz_spreadsheet"

    def test_get_provenance_not_found(self, test_client):
        """GET /api/v1/provenance/{id} returns 404 for non-existent UUID."""
        non_existent_id = uuid.uuid4()
        with patch(
            "api.routes.provenance.get_provenance",
            AsyncMock(return_value=None),
        ):
            response = test_client.get(f"/api/v1/provenance/{non_existent_id}")
        assert response.status_code == 404

    def test_query_provenance_by_source_type(self, test_client):
        """GET /api/v1/provenance?source_type=kazvodhoz_spreadsheet returns filtered list."""
        mock_list = [self._mock_provenance(source_type="kazvodhoz_spreadsheet")]
        with patch(
            "api.routes.provenance.query_provenance",
            AsyncMock(return_value=mock_list),
        ):
            response = test_client.get(
                "/api/v1/provenance?source_type=kazvodhoz_spreadsheet"
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["source_type"] == "kazvodhoz_spreadsheet"

    def test_query_provenance_by_confidence(self, test_client):
        """GET /api/v1/provenance?confidence_level=HIGH returns filtered list."""
        mock_list = [self._mock_provenance(confidence_level="HIGH")]
        with patch(
            "api.routes.provenance.query_provenance",
            AsyncMock(return_value=mock_list),
        ):
            response = test_client.get(
                "/api/v1/provenance?confidence_level=HIGH"
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["confidence_level"] == "HIGH"


class TestProvenanceFKEnforcement:
    """Test that provenance_id FK is enforced (DATA-07)."""

    @pytest.mark.integration
    async def test_fact_has_provenance(self):
        """Creating a StructureFactModel without provenance_id raises IntegrityError.

        This proves the nullable=False FK enforcement for DATA-07:
        every fact must have a provenance record.
        """
        from sqlalchemy.exc import IntegrityError

        from api.infrastructure.database import async_session
        from api.models.structure import StructureFactModel

        # Try to create a fact without provenance_id — should fail
        fact = StructureFactModel(
            structure_id=uuid.uuid4(),
            attribute_name="condition",
            attribute_value={"value": "good"},
            # provenance_id intentionally omitted
        )
        with pytest.raises(IntegrityError):
            async with async_session() as session:
                async with session.begin():
                    session.add(fact)
