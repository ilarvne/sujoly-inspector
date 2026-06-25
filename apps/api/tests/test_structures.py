"""Tests for structure CRUD + search endpoints.

Tests cover:
- POST /api/v1/structures → 201 with structure fields (D-13)
- GET /api/v1/structures/{id} → 200 with structure fields (D-13)
- GET /api/v1/structures/{id} → 404 for non-existent (D-13)
- GET /api/v1/structures?offset=0&limit=10 → paginated list with total (D-16)
- GET /api/v1/structures?type=canal&district=... → filtered list (D-16)
- GET /api/v1/structures/search?q=канал&lang=ru → FTS ranked results (D-12, D-14)
- GET /api/v1/structures/search?q=канал+42 → fuzzy/partial match (D-12)
- GET /api/v1/structures/search?q=Иртыш&lang=ru&type=canal → combined FTS + trigram + filter (D-12)
- GET /api/v1/structures?format=geojson → GeoJSON FeatureCollection (D-16)
- GET /api/v1/structures?bbox=60,40,80,50 → spatial filter (D-14, D-16)
- PUT /api/v1/structures/{id} → 200 with updated fields + provenance (D-13)
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStructureEndpoints:
    """Tests for /api/v1/structures CRUD + search endpoints."""

    def _mock_structure(self, **overrides):
        """Create a mock StructureModel instance with all response fields."""
        defaults = {
            "id": uuid.uuid4(),
            "name_ru": "Канал 1",
            "name_kk": None,
            "name_en": None,
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

    # ------------------------------------------------------------------
    # CRUD tests
    # ------------------------------------------------------------------

    def test_create_structure(self, test_client):
        """POST /api/v1/structures returns 201 with id, name_ru, type, provenance_id."""
        mock_struct = self._mock_structure()
        prov_id = uuid.uuid4()
        with patch(
            "api.routes.structures.create_structure",
            AsyncMock(return_value=mock_struct),
        ):
            response = test_client.post(
                f"/api/v1/structures?provenance_id={prov_id}",
                json={
                    "type": "canal",
                    "name_ru": "Канал 1",
                    "district": "Район 1",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name_ru"] == "Канал 1"
        assert data["type"] == "canal"
        assert "provenance_id" in data

    def test_get_structure(self, test_client):
        """GET /api/v1/structures/{id} returns 200 with structure fields."""
        struct_id = uuid.uuid4()
        mock_struct = self._mock_structure(id=struct_id)
        with patch(
            "api.routes.structures.get_structure",
            AsyncMock(return_value=mock_struct),
        ):
            response = test_client.get(f"/api/v1/structures/{struct_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(struct_id)
        assert data["type"] == "canal"
        assert data["name_ru"] == "Канал 1"

    def test_get_structure_not_found(self, test_client):
        """GET /api/v1/structures/{id} returns 404 for non-existent UUID."""
        non_existent_id = uuid.uuid4()
        with patch(
            "api.routes.structures.get_structure",
            AsyncMock(return_value=None),
        ):
            response = test_client.get(f"/api/v1/structures/{non_existent_id}")
        assert response.status_code == 404

    def test_update_structure(self, test_client):
        """PUT /api/v1/structures/{id} returns 200 with updated fields."""
        struct_id = uuid.uuid4()
        mock_updated = self._mock_structure(
            id=struct_id, name_ru="Updated Canal", wear_percentage=80.0
        )
        prov_id = uuid.uuid4()
        with patch(
            "api.routes.structures.update_structure",
            AsyncMock(return_value=mock_updated),
        ):
            response = test_client.put(
                f"/api/v1/structures/{struct_id}?provenance_id={prov_id}",
                json={"name_ru": "Updated Canal", "wear_percentage": 80.0},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["name_ru"] == "Updated Canal"
        assert data["wear_percentage"] == 80.0

    # ------------------------------------------------------------------
    # List + filter + pagination tests
    # ------------------------------------------------------------------

    def test_list_pagination(self, test_client, mock_structure_list):
        """GET /api/v1/structures?offset=0&limit=10 returns paginated list with total."""
        with patch(
            "api.routes.structures.list_structures",
            AsyncMock(return_value=(mock_structure_list, 3)),
        ):
            response = test_client.get(
                "/api/v1/structures?offset=0&limit=10"
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 3
        assert data["offset"] == 0
        assert data["limit"] == 10
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 3

    def test_filter_structures(self, test_client, mock_structure_list):
        """GET /api/v1/structures?type=canal&district=Район+1 returns filtered list."""
        with patch(
            "api.routes.structures.list_structures",
            AsyncMock(return_value=(mock_structure_list, 2)),
        ) as mock_list:
            response = test_client.get(
                "/api/v1/structures?type=canal&district=%D0%A0%D0%B0%D0%B9%D0%BE%D0%BD+1"
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        # Verify filters dict was passed to service
        call_kwargs = mock_list.call_args
        filters = (
            call_kwargs.kwargs.get("filters")
            if call_kwargs.kwargs
            else call_kwargs.args[0]
        )
        assert filters.get("type") == "canal"

    def test_list_geojson(self, test_client, mock_structure_list):
        """GET /api/v1/structures?format=geojson returns GeoJSON FeatureCollection."""
        with patch(
            "api.routes.structures.list_structures",
            AsyncMock(return_value=(mock_structure_list, 3)),
        ):
            response = test_client.get(
                "/api/v1/structures?format=geojson"
            )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert isinstance(data["features"], list)
        assert len(data["features"]) == 3
        # Each feature should have type, geometry, properties
        feature = data["features"][0]
        assert feature["type"] == "Feature"
        assert "geometry" in feature
        assert "properties" in feature

    def test_bbox_filter(self, test_client, mock_structure_list):
        """GET /api/v1/structures?bbox=60,40,80,50 returns filtered list without error."""
        with patch(
            "api.routes.structures.list_structures",
            AsyncMock(return_value=(mock_structure_list, 3)),
        ):
            response = test_client.get(
                "/api/v1/structures?bbox=60,40,80,50"
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    # ------------------------------------------------------------------
    # Search tests (FTS + trigram fuzzy matching)
    # ------------------------------------------------------------------

    def test_fts_search(self, test_client, mock_search_results):
        """GET /api/v1/structures/search?q=канал&lang=ru returns ranked results with match_score."""
        with patch(
            "api.routes.structures.search_structures",
            AsyncMock(return_value=(mock_search_results, 1)),
        ):
            response = test_client.get(
                "/api/v1/structures/search?q=%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB&lang=ru"
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1
        assert "match_score" in data["items"][0]
        assert data["items"][0]["match_score"] == 0.85

    def test_fuzzy_search(self, test_client, mock_search_results):
        """GET /api/v1/structures/search?q=канал+42 returns partial/typo match results."""
        with patch(
            "api.routes.structures.search_structures",
            AsyncMock(return_value=(mock_search_results, 1)),
        ):
            response = test_client.get(
                "/api/v1/structures/search?q=%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB+42&lang=ru"
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "match_score" in data["items"][0]

    def test_combined_search(self, test_client, mock_search_results):
        """GET /api/v1/structures/search?q=Иртыш&lang=ru&type=canal combines FTS + trigram + filter."""
        with patch(
            "api.routes.structures.search_structures",
            AsyncMock(return_value=(mock_search_results, 1)),
        ) as mock_search:
            response = test_client.get(
                "/api/v1/structures/search?q=%D0%98%D1%80%D1%82%D1%8B%D1%88&lang=ru&type=canal"
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        # Verify type filter was passed to service
        call_kwargs = mock_search.call_args
        filters = (
            call_kwargs.kwargs.get("filters")
            if call_kwargs.kwargs
            else call_kwargs.args[2]
        )
        assert filters.get("type") == "canal"
