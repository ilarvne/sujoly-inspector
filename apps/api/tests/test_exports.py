"""Tests for trilingual export endpoints (CSV/GeoJSON/PDF) per RISK-08.

Tests cover:
- GET /api/v1/export/structures?format=csv&lang=ru → 200, text/csv, Content-Disposition
- CSV body starts with UTF-8 BOM (\xef\xbb\xbf)
- CSV with lang=ru has Russian column headers
- CSV rows include inspection_interval, repair_status, composite_score
- GET /api/v1/export/structures?format=csv&type=canal → filters by structure type
- GET /api/v1/export/structures?format=geojson&lang=ru → 200, FeatureCollection
- GeoJSON features include risk fields in properties
- GET /api/v1/export/inspection-report/{id}?lang=ru → 200, application/pdf
- GET /api/v1/export/inspection-report/{nonexistent} → 404
- GET with lang=kk → Kazakh headers; lang=en → English headers
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestExportEndpoints:
    """Tests for /api/v1/export endpoints (CSV/GeoJSON/PDF)."""

    def _mock_structure(self, **overrides):
        """Create a mock StructureModel with all response fields."""
        from datetime import datetime, timezone

        defaults = {
            "id": uuid.uuid4(),
            "name_ru": "Канал 1",
            "name_kk": "Арна 1",
            "name_en": "Canal 1",
            "type": "canal",
            "district": "Район 1",
            "water_source": "р. Иртыш",
            "technical_condition": "удовлетворительное",
            "wear_percentage": 45.0,
            "commissioning_year": 1973,
            "cadastral_number": "01-001",
            "structure_count": 5,
            "geometry": None,
            "provenance_id": uuid.uuid4(),
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        mock = MagicMock()
        for key, val in defaults.items():
            setattr(mock, key, val)
        return mock

    def _mock_risk_assessment(self, **overrides):
        """Create a mock RiskAssessmentModel with risk fields."""
        defaults = {
            "condition_score": 65.0,
            "consequence_factor": 1.2,
            "seasonal_modifier": 1.0,
            "staleness_modifier": 1.0,
            "composite_score": 78.0,
            "inspection_interval": "180d",
            "repair_status": "inspection_required",
            "red_flags": [],
            "contributing_factors": {},
            "weak_evidence_reasons": [],
        }
        defaults.update(overrides)
        mock = MagicMock()
        for key, val in defaults.items():
            setattr(mock, key, val)
        return mock

    def _mock_inspection(self, **overrides):
        """Create a mock InspectionModel with photos."""
        from datetime import datetime, timezone

        photo = MagicMock()
        photo.minio_bucket = "sujoly-photos"
        photo.minio_object_key = "photos/test.jpg"
        photo.caption = "Overview photo"
        photo.photo_type = "overview"

        defaults = {
            "id": uuid.uuid4(),
            "structure_id": uuid.uuid4(),
            "inspection_date": "2026-06-01",
            "inspector_name": "Inspector One",
            "inspector_role": "inspector",
            "findings": "Structure in satisfactory condition",
            "condition_at_inspection": "удовлетворительное",
            "condition_score_at_inspection": 65.0,
            "red_flags_observed": [],
            "provenance_id": uuid.uuid4(),
            "created_at": datetime.now(timezone.utc),
            "photos": [photo],
        }
        defaults.update(overrides)
        mock = MagicMock()
        for key, val in defaults.items():
            setattr(mock, key, val)
        return mock

    def test_export_csv(self, test_client):
        """GET /api/v1/export/structures?format=csv&lang=ru returns 200, text/csv, Content-Disposition."""
        mock_struct = self._mock_structure()
        mock_risk = self._mock_risk_assessment()

        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response = test_client.get(
                "/api/v1/export/structures?format=csv&lang=ru"
            )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers.get("content-disposition", "")

    def test_export_csv_has_bom(self, test_client):
        """CSV response body starts with UTF-8 BOM (\\xef\\xbb\\xbf)."""
        mock_struct = self._mock_structure()
        mock_risk = self._mock_risk_assessment()

        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response = test_client.get(
                "/api/v1/export/structures?format=csv&lang=ru"
            )

        assert response.content.startswith(b"\xef\xbb\xbf"), (
            "CSV export must start with UTF-8 BOM for Excel Cyrillic compatibility (D-20)"
        )

    def test_export_csv_russian_headers(self, test_client):
        """CSV with lang=ru contains Russian column headers."""
        mock_struct = self._mock_structure()
        mock_risk = self._mock_risk_assessment()

        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response = test_client.get(
                "/api/v1/export/structures?format=csv&lang=ru"
            )

        # Decode after BOM
        body = response.content.decode("utf-8-sig")
        assert "Название" in body or "Тип" in body or "Район" in body, (
            "CSV with lang=ru must contain Russian column headers"
        )

    def test_export_csv_includes_risk_fields(self, test_client):
        """CSV rows include inspection_interval, repair_status, composite_score columns."""
        mock_struct = self._mock_structure()
        mock_risk = self._mock_risk_assessment(
            inspection_interval="180d",
            repair_status="inspection_required",
            composite_score=78.0,
        )

        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response = test_client.get(
                "/api/v1/export/structures?format=csv&lang=ru"
            )

        body = response.content.decode("utf-8-sig")
        assert "180d" in body
        assert "inspection_required" in body
        assert "78" in body

    def test_export_csv_filters(self, test_client):
        """GET /api/v1/export/structures?format=csv&type=canal filters by structure type."""
        mock_struct = self._mock_structure()
        mock_risk = self._mock_risk_assessment()

        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ) as mock_list, patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response = test_client.get(
                "/api/v1/export/structures?format=csv&type=canal"
            )

        assert response.status_code == 200
        # Verify list_structures was called with type filter
        call_args = mock_list.call_args
        filters = call_args[1].get("filters", call_args[0][0] if call_args[0] else {})
        assert filters.get("type") == "canal" or any(
            "canal" in str(a) for a in call_args[0]
        )

    def test_export_geojson(self, test_client):
        """GET /api/v1/export/structures?format=geojson&lang=ru returns 200, FeatureCollection."""
        mock_struct = self._mock_structure()
        mock_risk = self._mock_risk_assessment()

        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response = test_client.get(
                "/api/v1/export/structures?format=geojson&lang=ru"
            )

        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == "FeatureCollection"
        assert "features" in data

    def test_export_geojson_has_risk_properties(self, test_client):
        """GeoJSON features' properties include inspection_interval, repair_status, composite_score."""
        mock_struct = self._mock_structure()
        mock_risk = self._mock_risk_assessment(
            inspection_interval="180d",
            repair_status="inspection_required",
            composite_score=78.0,
        )

        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response = test_client.get(
                "/api/v1/export/structures?format=geojson&lang=ru"
            )

        data = response.json()
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "inspection_interval" in props
        assert "repair_status" in props
        assert "composite_score" in props

    def test_export_pdf(self, test_client):
        """GET /api/v1/export/inspection-report/{id}?lang=ru returns 200, application/pdf."""
        inspection_id = uuid.uuid4()
        mock_struct = self._mock_structure()
        mock_inspection = self._mock_inspection(id=inspection_id)
        mock_risk = self._mock_risk_assessment()

        with patch(
            "api.services.inspection_service.get_inspection",
            AsyncMock(return_value=mock_inspection),
        ), patch(
            "api.services.structure_service.get_structure",
            AsyncMock(return_value=mock_struct),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ), patch(
            "api.services.export_service.export_inspection_report_pdf",
            AsyncMock(
                return_value=MagicMock(
                    media_type="application/pdf",
                    headers={"content-disposition": f"attachment; filename=inspection_{inspection_id}_ru.pdf"},
                )
            ),
        ):
            response = test_client.get(
                f"/api/v1/export/inspection-report/{inspection_id}?lang=ru"
            )

        assert response.status_code == 200

    def test_export_pdf_not_found(self, test_client):
        """GET /api/v1/export/inspection-report/{nonexistent_id} returns 404."""
        nonexistent_id = uuid.uuid4()

        with patch(
            "api.services.inspection_service.get_inspection",
            AsyncMock(return_value=None),
        ):
            response = test_client.get(
                f"/api/v1/export/inspection-report/{nonexistent_id}?lang=ru"
            )

        assert response.status_code == 404

    def test_export_trilingual(self, test_client):
        """GET with lang=kk returns Kazakh headers in CSV; GET with lang=en returns English headers."""
        mock_struct = self._mock_structure()
        mock_risk = self._mock_risk_assessment()

        # Test Kazakh
        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response_kk = test_client.get(
                "/api/v1/export/structures?format=csv&lang=kk"
            )

        body_kk = response_kk.content.decode("utf-8-sig")
        assert "Атауы" in body_kk or "Түрі" in body_kk or "Аудан" in body_kk, (
            "CSV with lang=kk must contain Kazakh column headers"
        )

        # Test English
        with patch(
            "api.services.structure_service.list_structures",
            AsyncMock(return_value=([mock_struct], 1)),
        ), patch(
            "api.services.risk_service.get_latest_assessment",
            AsyncMock(return_value=mock_risk),
        ):
            response_en = test_client.get(
                "/api/v1/export/structures?format=csv&lang=en"
            )

        body_en = response_en.content.decode("utf-8-sig")
        assert "Name" in body_en or "Type" in body_en or "District" in body_en, (
            "CSV with lang=en must contain English column headers"
        )
