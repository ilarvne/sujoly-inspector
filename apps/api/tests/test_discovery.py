"""Tests for OSM Overpass discovery service and candidate CRUD endpoints.

Tests cover:
- Overpass QL query building
- OSM element parsing into CandidateCreate schemas
- discover_from_osm with mocked Overpass API
- discover_candidates with dedup
- discover_and_match (discovery + auto-matching pipeline)
- Candidate CRUD endpoints (list, get, discover, review, delete)
- Match endpoints (match all, match single)
- Celery run_discovery_pipeline task
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.schemas.candidates import (
    CandidateCreate,
    CandidateListResponse,
    CandidateMatchResult,
    CandidateResponse,
    CandidateReviewRequest,
)
from api.services.discovery_service import (
    DiscoveryService,
    _build_overpass_query,
    _parse_osm_element,
)
from api.services.matching_service import MatchingService


# ---------------------------------------------------------------------------
# Overpass query building tests
# ---------------------------------------------------------------------------


class TestBuildOverpassQuery:
    """Tests for _build_overpass_query function."""

    def test_basic_query_with_bbox(self):
        """Query is built with default tags for a given bbox."""
        query = _build_overpass_query("68.0,42.0,72.0,45.0")
        assert "[out:json]" in query
        assert "42.0,68.0,45.0,72.0" in query  # Overpass bbox: S,W,N,E
        assert '"waterway"="canal"' in query
        assert "out center" in query

    def test_custom_tags(self):
        """Query uses provided tags instead of defaults."""
        query = _build_overpass_query(
            "68.0,42.0,72.0,45.0",
            tags=["waterway=dam"],
        )
        assert '"waterway"="dam"' in query
        assert '"waterway"="canal"' not in query

    def test_invalid_bbox_raises(self):
        """ValueError raised for invalid bbox format."""
        with pytest.raises(ValueError, match="exactly 4 values"):
            _build_overpass_query("68.0,42.0")

    def test_compound_tag_query(self):
        """Compound tag with '+' produces chained key filters."""
        query = _build_overpass_query(
            "68.0,42.0,72.0,45.0",
            tags=["natural=water+water=reservoir"],
        )
        assert '["natural"="water"]["water"="reservoir"]' in query


# ---------------------------------------------------------------------------
# OSM element parsing tests
# ---------------------------------------------------------------------------


class TestParseOsmElement:
    """Tests for _parse_osm_element function."""

    def test_named_node_with_tags(self):
        """Named OSM node with waterway tag produces CandidateCreate."""
        element = {
            "type": "node",
            "id": 123456,
            "lat": 42.9,
            "lon": 71.4,
            "tags": {
                "name": "Плотина Талас",
                "waterway": "dam",
            },
        }
        result = _parse_osm_element(element)
        assert result is not None
        assert result.name == "Плотина Талас"
        assert result.source_type == "osm"
        assert result.source_id == "node/123456"
        assert result.latitude == 42.9
        assert result.longitude == 71.4
        assert result.type == "dam"
        assert result.evidence["osm"]["tags"]["waterway"] == "dam"

    def test_way_with_center(self):
        """OSM way with center coordinates produces CandidateCreate."""
        element = {
            "type": "way",
            "id": 789012,
            "center": {"lat": 43.1, "lon": 71.8},
            "tags": {
                "name:ru": "Канал Шу",
                "waterway": "canal",
            },
        }
        result = _parse_osm_element(element)
        assert result is not None
        assert result.name == "Канал Шу"
        assert result.source_id == "way/789012"
        assert result.latitude == 43.1
        assert result.longitude == 71.8
        assert result.type == "canal"

    def test_unnamed_element_returns_none(self):
        """Unnamed OSM element (no name tags) returns None."""
        element = {
            "type": "node",
            "id": 999,
            "lat": 42.0,
            "lon": 71.0,
            "tags": {"waterway": "dam"},
        }
        result = _parse_osm_element(element)
        assert result is None

    def test_no_tags_returns_none(self):
        """Element without tags returns None."""
        element = {"type": "node", "id": 1, "lat": 42.0, "lon": 71.0}
        result = _parse_osm_element(element)
        assert result is None

    def test_inferred_type_sluice_gate(self):
        """waterway=sluice_gate maps to inferred type 'sluice_gate'."""
        element = {
            "type": "node",
            "id": 100,
            "lat": 42.0,
            "lon": 71.0,
            "tags": {"name": "Шлюз", "waterway": "sluice_gate"},
        }
        result = _parse_osm_element(element)
        assert result is not None
        assert result.type == "sluice_gate"

    def test_water_source_from_river_tag(self):
        """waterway:name and river tags map to water_source field."""
        element = {
            "type": "way",
            "id": 200,
            "center": {"lat": 42.0, "lon": 71.0},
            "tags": {
                "name": "Канал Иртыш",
                "waterway": "canal",
                "river": "Иртыш",
            },
        }
        result = _parse_osm_element(element)
        assert result is not None
        assert result.water_source == "Иртыш"

    def test_name_en_fallback(self):
        """name:en is used when name and name:ru are absent."""
        element = {
            "type": "node",
            "id": 300,
            "lat": 42.0,
            "lon": 71.0,
            "tags": {
                "name:en": "Talas Dam",
                "waterway": "dam",
            },
        }
        result = _parse_osm_element(element)
        assert result is not None
        assert result.name == "Talas Dam"


# ---------------------------------------------------------------------------
# DiscoveryService.discover_from_osm tests (mocked Overpass)
# ---------------------------------------------------------------------------


class TestDiscoverFromOsm:
    """Tests for DiscoveryService.discover_from_osm with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_discover_from_osm_success(self):
        """discover_from_osm parses Overpass response into CandidateCreate list."""
        overpass_response = {
            "elements": [
                {
                    "type": "node",
                    "id": 111,
                    "lat": 42.9,
                    "lon": 71.4,
                    "tags": {
                        "name": "Плотина 1",
                        "waterway": "dam",
                    },
                },
                {
                    "type": "way",
                    "id": 222,
                    "center": {"lat": 43.1, "lon": 71.8},
                    "tags": {
                        "name": "Канал 1",
                        "waterway": "canal",
                    },
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = overpass_response
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("api.services.discovery_service.httpx.AsyncClient", return_value=mock_client):
            service = DiscoveryService()
            results = await service.discover_from_osm("68.0,42.0,72.0,45.0")

        assert len(results) == 2
        assert results[0].name == "Плотина 1"
        assert results[1].name == "Канал 1"

    @pytest.mark.asyncio
    async def test_discover_from_osm_filters_unnamed(self):
        """discover_from_osm skips unnamed elements."""
        overpass_response = {
            "elements": [
                {
                    "type": "node",
                    "id": 111,
                    "lat": 42.9,
                    "lon": 71.4,
                    "tags": {"waterway": "dam"},
                },
                {
                    "type": "node",
                    "id": 222,
                    "lat": 43.0,
                    "lon": 71.5,
                    "tags": {"name": "Named Dam", "waterway": "dam"},
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = overpass_response
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("api.services.discovery_service.httpx.AsyncClient", return_value=mock_client):
            service = DiscoveryService()
            results = await service.discover_from_osm("68.0,42.0,72.0,45.0")

        assert len(results) == 1
        assert results[0].name == "Named Dam"


# ---------------------------------------------------------------------------
# DiscoveryService.discover_candidates tests (mocked DB)
# ---------------------------------------------------------------------------


class TestDiscoverCandidates:
    """Tests for DiscoveryService.discover_candidates with dedup."""

    @pytest.mark.asyncio
    async def test_discover_candidates_persists_new(self):
        """discover_candidates creates new candidates in DB."""
        osm_results = [
            CandidateCreate(
                source_type="osm",
                source_id="node/111",
                name="New Dam",
                latitude=42.9,
                longitude=71.4,
                type="dam",
                evidence={"osm": {"tags": {"waterway": "dam"}}},
            ),
        ]

        # Mock the DB session
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock(
            side_effect=lambda m: setattr(m, "id", uuid.uuid4())
        )
        mock_session.begin = MagicMock()

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_async_session = MagicMock(return_value=mock_cm)

        with patch(
            "api.services.discovery_service.async_session", mock_async_session
        ), patch.object(
            DiscoveryService, "discover_from_osm", return_value=osm_results
        ):
            service = DiscoveryService()
            results = await service.discover_candidates(bbox="68.0,42.0,72.0,45.0")

        assert len(results) == 1
        # Verify session.add was called for provenance and candidate
        assert mock_session.add.call_count >= 2

    @pytest.mark.asyncio
    async def test_discover_candidates_dedup_skips_existing(self):
        """discover_candidates skips candidates with existing source_id."""
        osm_results = [
            CandidateCreate(
                source_type="osm",
                source_id="node/111",
                name="Existing Dam",
                latitude=42.9,
                longitude=71.4,
                type="dam",
                evidence={"osm": {"tags": {"waterway": "dam"}}},
            ),
        ]

        # Mock that the source_id already exists
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=MagicMock())
            )
        )
        mock_session.flush = AsyncMock()
        mock_session.begin = MagicMock()

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_async_session = MagicMock(return_value=mock_cm)

        with patch(
            "api.services.discovery_service.async_session", mock_async_session
        ), patch.object(
            DiscoveryService, "discover_from_osm", return_value=osm_results
        ):
            service = DiscoveryService()
            results = await service.discover_candidates(bbox="68.0,42.0,72.0,45.0")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_discover_candidates_unsupported_source_raises(self):
        """discover_candidates raises ValueError for unsupported source."""
        service = DiscoveryService()
        with pytest.raises(ValueError, match="Unsupported discovery source"):
            await service.discover_candidates(bbox="68.0,42.0,72.0,45.0", source="satellite")


# ---------------------------------------------------------------------------
# Candidate CRUD endpoint tests
# ---------------------------------------------------------------------------


def _make_mock_candidate(**overrides):
    """Create a mock CandidateModel for route tests."""
    defaults = {
        "id": uuid.uuid4(),
        "name": "OSM Dam Candidate",
        "source_type": "osm",
        "source_id": "way/123456789",
        "geometry": None,
        "match_status": "unmatched",
        "matched_structure_id": None,
        "confidence": "MEDIUM",
        "confidence_score": 0.65,
        "evidence": {"osm": {"tags": {"waterway": "dam"}, "distance_m": 50}},
        "district": "Жамбылский район",
        "water_source": "р. Талас",
        "type": "dam",
        "review_notes": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "provenance_id": uuid.uuid4(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock


class TestCandidateListEndpoint:
    """Tests for GET /candidates endpoint."""

    def test_list_candidates_success(self, test_client):
        """GET /candidates returns list of candidates."""
        mock_candidates = [_make_mock_candidate(), _make_mock_candidate(name="Second")]

        with patch(
            "api.routes.candidates._list_candidates_from_db",
            AsyncMock(return_value=(mock_candidates, 2)),
        ):
            response = test_client.get("/api/v1/candidates")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_candidates_with_filters(self, test_client):
        """GET /candidates with match_status filter passes through."""
        with patch(
            "api.routes.candidates._list_candidates_from_db",
            AsyncMock(return_value=([], 0)),
        ):
            response = test_client.get("/api/v1/candidates?match_status=unmatched")

        assert response.status_code == 200


class TestCandidateGetEndpoint:
    """Tests for GET /candidates/{id} endpoint."""

    def test_get_candidate_found(self, test_client):
        """GET /candidates/{id} returns candidate when found."""
        candidate = _make_mock_candidate()

        with patch(
            "api.routes.candidates._get_candidate_by_id",
            AsyncMock(return_value=candidate),
        ):
            response = test_client.get(f"/api/v1/candidates/{candidate.id}")

        assert response.status_code == 200

    def test_get_candidate_not_found(self, test_client):
        """GET /candidates/{id} returns 404 when not found."""
        with patch(
            "api.routes.candidates._get_candidate_by_id",
            AsyncMock(return_value=None),
        ):
            response = test_client.get(f"/api/v1/candidates/{uuid.uuid4()}")

        assert response.status_code == 404


class TestCandidateReviewEndpoint:
    """Tests for POST /candidates/{id}/review endpoint."""

    def test_review_candidate_success(self, test_client):
        """POST /candidates/{id}/review updates match_status and review fields."""
        candidate_id = uuid.uuid4()
        updated_candidate = _make_mock_candidate(
            id=candidate_id,
            match_status="matched",
            matched_structure_id=uuid.uuid4(),
            review_notes="Confirmed match",
            reviewed_by=uuid.uuid4(),
            reviewed_at=datetime.now(timezone.utc),
        )

        review_data = {
            "match_status": "matched",
            "matched_structure_id": str(updated_candidate.matched_structure_id),
            "review_notes": "Confirmed match",
        }

        with patch(
            "api.routes.candidates._review_candidate",
            AsyncMock(return_value=updated_candidate),
        ):
            response = test_client.post(
                f"/api/v1/candidates/{candidate_id}/review",
                json=review_data,
            )

        assert response.status_code == 200

    def test_review_candidate_not_found(self, test_client):
        """POST /candidates/{id}/review returns 404 when candidate not found."""
        candidate_id = uuid.uuid4()

        with patch(
            "api.routes.candidates._review_candidate",
            AsyncMock(return_value=None),
        ):
            response = test_client.post(
                f"/api/v1/candidates/{candidate_id}/review",
                json={"match_status": "rejected", "review_notes": "Not found test"},
            )

        assert response.status_code == 404


class TestCandidateDeleteEndpoint:
    """Tests for DELETE /candidates/{id} endpoint."""

    def test_delete_candidate_success(self, test_client):
        """DELETE /candidates/{id} returns deleted status."""
        with patch(
            "api.routes.candidates._delete_candidate_by_id",
            AsyncMock(return_value=True),
        ):
            response = test_client.delete(f"/api/v1/candidates/{uuid.uuid4()}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_candidate_not_found(self, test_client):
        """DELETE /candidates/{id} returns 404 when not found."""
        with patch(
            "api.routes.candidates._delete_candidate_by_id",
            AsyncMock(return_value=False),
        ):
            response = test_client.delete(f"/api/v1/candidates/{uuid.uuid4()}")

        assert response.status_code == 404


class TestDiscoverEndpoint:
    """Tests for POST /candidates/discover endpoint."""

    def test_discover_endpoint_success(self, test_client):
        """POST /candidates/discover creates candidates from OSM."""
        mock_candidate = _make_mock_candidate()

        with patch(
            "api.routes.candidates.DiscoveryService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.discover_candidates = AsyncMock(return_value=[mock_candidate])
            MockService.return_value = mock_service

            response = test_client.post(
                "/api/v1/candidates/discover?bbox=68.0,42.0,72.0,45.0",
            )

        assert response.status_code == 201

    def test_discover_endpoint_invalid_bbox(self, test_client):
        """POST /candidates/discover returns 400 for invalid bbox."""
        with patch(
            "api.routes.candidates.DiscoveryService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.discover_candidates = AsyncMock(
                side_effect=ValueError("bbox must contain exactly 4 values")
            )
            MockService.return_value = mock_service

            response = test_client.post(
                "/api/v1/candidates/discover?bbox=invalid",
            )

        assert response.status_code == 400

    def test_discover_endpoint_overpass_error(self, test_client):
        """POST /candidates/discover returns 502 when Overpass API fails."""
        with patch(
            "api.routes.candidates.DiscoveryService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.discover_candidates = AsyncMock(
                side_effect=Exception("Overpass API timeout")
            )
            MockService.return_value = mock_service

            response = test_client.post(
                "/api/v1/candidates/discover?bbox=68.0,42.0,72.0,45.0",
            )

        assert response.status_code == 502


# ---------------------------------------------------------------------------
# discover_and_match tests (integrated pipeline)
# ---------------------------------------------------------------------------


class TestDiscoverAndMatch:
    """Tests for DiscoveryService.discover_and_match integrated pipeline."""

    @pytest.mark.asyncio
    async def test_discover_and_match_with_candidates(self):
        """discover_and_match runs matching after discovery."""
        mock_candidate = MagicMock()
        mock_candidate.id = uuid.uuid4()
        mock_candidate.name = "Test Dam"
        mock_candidate.geometry = "SRID=4326;POINT(71.4 42.9)"

        match_result = CandidateMatchResult(
            candidate_id=mock_candidate.id,
            match_status="matched",
            confidence="HIGH",
            confidence_score=0.85,
            matched_structure_id=uuid.uuid4(),
            evidence={"spatial_distance_m": 50.0, "name_similarity": 0.9, "attribute_matches": 3},
        )

        # Mock the update session
        update_session = MagicMock()
        update_session.execute = AsyncMock(return_value=None)
        update_session.begin = MagicMock()
        update_cm = MagicMock()
        update_cm.__aenter__ = AsyncMock(return_value=update_session)
        update_cm.__aexit__ = AsyncMock(return_value=None)

        with patch.object(
            DiscoveryService, "discover_candidates",
            AsyncMock(return_value=[mock_candidate]),
        ), patch.object(
            MatchingService, "match_candidate",
            AsyncMock(return_value=match_result),
        ), patch(
            "api.services.discovery_service.async_session",
            MagicMock(return_value=update_cm),
        ):
            service = DiscoveryService()
            results = await service.discover_and_match(bbox="68.0,42.0,72.0,45.0")

        assert len(results) == 1
        candidate, mr = results[0]
        assert mr.match_status == "matched"
        assert mr.confidence == "HIGH"

    @pytest.mark.asyncio
    async def test_discover_and_match_empty(self):
        """discover_and_match returns empty when no candidates discovered."""
        with patch.object(
            DiscoveryService, "discover_candidates",
            AsyncMock(return_value=[]),
        ):
            service = DiscoveryService()
            results = await service.discover_and_match(bbox="68.0,42.0,72.0,45.0")

        assert len(results) == 0


# ---------------------------------------------------------------------------
# Match endpoint tests
# ---------------------------------------------------------------------------


class TestMatchAllEndpoint:
    """Tests for POST /candidates/match endpoint."""

    def test_match_all_success(self, test_client):
        """POST /candidates/match returns match results for all unmatched."""
        match_results = [
            CandidateMatchResult(
                candidate_id=uuid.uuid4(),
                match_status="new_candidate",
                confidence="LOW",
                confidence_score=0.1,
                matched_structure_id=None,
                evidence={"reason": "no_nearby_structures"},
            ),
        ]

        with patch(
            "api.services.matching_service.MatchingService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.match_all_unmatched = AsyncMock(return_value=match_results)
            MockService.return_value = mock_service

            response = test_client.post("/api/v1/candidates/match")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["match_status"] == "new_candidate"

    def test_match_all_error(self, test_client):
        """POST /candidates/match returns 500 on matching error."""
        with patch(
            "api.services.matching_service.MatchingService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.match_all_unmatched = AsyncMock(
                side_effect=Exception("DB connection lost")
            )
            MockService.return_value = mock_service

            response = test_client.post("/api/v1/candidates/match")

        assert response.status_code == 500


class TestMatchSingleEndpoint:
    """Tests for POST /candidates/{id}/match endpoint."""

    def test_match_single_success(self, test_client):
        """POST /candidates/{id}/match returns match result for candidate."""
        candidate_id = uuid.uuid4()
        mock_candidate = _make_mock_candidate(id=candidate_id)

        match_result = CandidateMatchResult(
            candidate_id=candidate_id,
            match_status="likely_match",
            confidence="MEDIUM",
            confidence_score=0.55,
            matched_structure_id=None,
            evidence={"spatial_distance_m": 200.0, "name_similarity": 0.5, "attribute_matches": 1},
        )

        # Mock the update session
        update_session = MagicMock()
        update_session.execute = AsyncMock(return_value=None)
        update_cm = MagicMock()
        update_cm.__aenter__ = AsyncMock(return_value=update_session)
        update_cm.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "api.routes.candidates._get_candidate_by_id",
            AsyncMock(return_value=mock_candidate),
        ), patch(
            "api.services.matching_service.MatchingService"
        ) as MockService, patch(
            "api.infrastructure.database.async_session",
            MagicMock(return_value=update_cm),
        ):
            mock_service = MagicMock()
            mock_service.match_candidate = AsyncMock(return_value=match_result)
            MockService.return_value = mock_service

            response = test_client.post(f"/api/v1/candidates/{candidate_id}/match")

        assert response.status_code == 200
        data = response.json()
        assert data["match_status"] == "likely_match"
        assert data["confidence"] == "MEDIUM"

    def test_match_single_not_found(self, test_client):
        """POST /candidates/{id}/match returns 404 when candidate not found."""
        candidate_id = uuid.uuid4()

        with patch(
            "api.routes.candidates._get_candidate_by_id",
            AsyncMock(return_value=None),
        ):
            response = test_client.post(f"/api/v1/candidates/{candidate_id}/match")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Celery run_discovery_pipeline task tests
# ---------------------------------------------------------------------------


class TestRunDiscoveryPipelineTask:
    """Tests for the Celery run_discovery_pipeline task."""

    def test_pipeline_discovers_and_matches(self):
        """run_discovery_pipeline returns summary with match results."""
        from api.tasks.celery_tasks import run_discovery_pipeline

        candidate_id = uuid.uuid4()
        mock_candidate = MagicMock()
        mock_candidate.id = candidate_id

        match_result = CandidateMatchResult(
            candidate_id=candidate_id,
            match_status="matched",
            confidence="HIGH",
            confidence_score=0.85,
            matched_structure_id=uuid.uuid4(),
            evidence={"spatial_distance_m": 50.0, "name_similarity": 0.9},
        )

        # Mock the update session
        update_session = MagicMock()
        update_session.execute = AsyncMock(return_value=None)
        update_session.begin = MagicMock()
        update_cm = MagicMock()
        update_cm.__aenter__ = AsyncMock(return_value=update_session)
        update_cm.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "api.services.discovery_service.DiscoveryService"
        ) as MockDiscovery, patch(
            "api.services.matching_service.MatchingService"
        ) as MockMatching, patch(
            "api.infrastructure.database.async_session",
            MagicMock(return_value=update_cm),
        ):
            mock_discovery = MagicMock()
            mock_discovery.discover_candidates = AsyncMock(return_value=[mock_candidate])
            MockDiscovery.return_value = mock_discovery

            mock_matching = MagicMock()
            mock_matching.match_candidate = AsyncMock(return_value=match_result)
            MockMatching.return_value = mock_matching

            result = run_discovery_pipeline(bbox="68.0,42.0,72.0,45.0")

        assert result["discovered"] == 1
        assert "matched" in result["matched_summary"]
        assert len(result["results"]) == 1
        assert result["results"][0]["match_status"] == "matched"

    def test_pipeline_empty_discovery(self):
        """run_discovery_pipeline returns zero counts when no candidates found."""
        from api.tasks.celery_tasks import run_discovery_pipeline

        with patch(
            "api.services.discovery_service.DiscoveryService"
        ) as MockDiscovery:
            mock_discovery = MagicMock()
            mock_discovery.discover_candidates = AsyncMock(return_value=[])
            MockDiscovery.return_value = mock_discovery

            result = run_discovery_pipeline(bbox="68.0,42.0,72.0,45.0")

        assert result["discovered"] == 0
        assert result["matched_summary"] == {}
        assert result["results"] == []
