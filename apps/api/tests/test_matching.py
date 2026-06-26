"""Tests for hierarchical matching engine.

Tests cover:
- compute_confidence with various signal combinations
- match_candidate with mock spatial/name results
- Match state assignment logic (DISC-03)
- match_all_unmatched batch processing
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.schemas.candidates import CandidateMatchResult
from api.services.matching_service import MatchingService, compute_confidence


# ---------------------------------------------------------------------------
# compute_confidence tests
# ---------------------------------------------------------------------------


class TestComputeConfidence:
    """Tests for the compute_confidence scoring function."""

    def test_perfect_match_high_confidence(self):
        """Perfect signals → HIGH confidence."""
        level, score = compute_confidence(
            spatial_dist=10.0,  # very close
            name_sim=0.95,  # nearly identical name
            attr_matches=3,  # all attributes match
        )
        assert level == "HIGH"
        assert score >= 0.7

    def test_likely_match_medium_confidence(self):
        """Moderate signals → MEDIUM confidence."""
        level, score = compute_confidence(
            spatial_dist=200.0,
            name_sim=0.5,
            attr_matches=1,
        )
        assert level == "MEDIUM"
        assert score >= 0.4

    def test_weak_signals_low_confidence(self):
        """Weak signals → LOW confidence."""
        level, score = compute_confidence(
            spatial_dist=490.0,
            name_sim=0.1,
            attr_matches=0,
        )
        assert level == "LOW"
        assert score < 0.4

    def test_no_name_similarity(self):
        """No name similarity pulls score down significantly."""
        level, score = compute_confidence(
            spatial_dist=50.0,
            name_sim=0.0,
            attr_matches=2,
        )
        # spatial component: 0.3 * (1 - 50/500) = 0.3 * 0.9 = 0.27
        # name component: 0.4 * 0 = 0
        # attr component: 0.3 * (2/3) = 0.2
        # total: 0.47 → MEDIUM
        assert level == "MEDIUM"
        assert 0.4 <= score < 0.7

    def test_close_spatial_no_attributes(self):
        """Close spatial but no name/attribute match → MEDIUM."""
        level, score = compute_confidence(
            spatial_dist=30.0,
            name_sim=0.4,
            attr_matches=0,
        )
        # spatial: 0.3 * (1 - 30/500) = 0.3 * 0.94 = 0.282
        # name: 0.4 * 0.4 = 0.16
        # attr: 0.3 * 0 = 0
        # total: 0.442 → MEDIUM
        assert level == "MEDIUM"

    def test_distance_clamped_at_500(self):
        """Distances > 500m are clamped, preventing negative spatial score."""
        level, score = compute_confidence(
            spatial_dist=800.0,
            name_sim=0.8,
            attr_matches=2,
        )
        # spatial: 0.3 * (1 - 500/500) = 0
        # name: 0.4 * 0.8 = 0.32
        # attr: 0.3 * (2/3) = 0.2
        # total: 0.52 → MEDIUM
        assert level == "MEDIUM"
        assert score >= 0.0

    def test_zero_distance(self):
        """Zero distance gives maximum spatial component."""
        level, score = compute_confidence(
            spatial_dist=0.0,
            name_sim=0.0,
            attr_matches=0,
        )
        # spatial: 0.3 * 1.0 = 0.3
        # name: 0
        # attr: 0
        # total: 0.3 → LOW
        assert level == "LOW"

    def test_exact_formula_values(self):
        """Verify exact formula computation for known inputs."""
        # score = 0.4 * 0.6 + 0.3 * (1 - 100/500) + 0.3 * (2/3)
        #       = 0.24 + 0.3 * 0.8 + 0.2
        #       = 0.24 + 0.24 + 0.2 = 0.68
        level, score = compute_confidence(
            spatial_dist=100.0,
            name_sim=0.6,
            attr_matches=2,
        )
        assert level == "MEDIUM"
        assert abs(score - 0.68) < 0.001

    def test_all_attributes_match(self):
        """All 3 attributes match gives full attribute component."""
        level, score = compute_confidence(
            spatial_dist=50.0,
            name_sim=0.8,
            attr_matches=3,
        )
        assert level == "HIGH"
        # spatial: 0.3 * 0.9 = 0.27
        # name: 0.4 * 0.8 = 0.32
        # attr: 0.3 * 1.0 = 0.3
        # total: 0.89
        assert abs(score - 0.89) < 0.001

    def test_score_clamped_to_one(self):
        """Score is clamped to max 1.0 even with extreme inputs."""
        level, score = compute_confidence(
            spatial_dist=0.0,
            name_sim=1.0,
            attr_matches=3,
        )
        assert score <= 1.0
        assert level == "HIGH"


# ---------------------------------------------------------------------------
# match_candidate tests (mocked DB)
# ---------------------------------------------------------------------------


def _make_mock_candidate(geometry=None, **overrides):
    """Create a mock CandidateModel with sensible defaults."""
    defaults = {
        "id": uuid.uuid4(),
        "name": "Плотина Талас",
        "source_type": "osm",
        "source_id": "node/111",
        "geometry": geometry,
        "match_status": "unmatched",
        "matched_structure_id": None,
        "confidence": "MEDIUM",
        "confidence_score": None,
        "evidence": {"osm": {"tags": {"waterway": "dam"}}},
        "district": "Жамбылский район",
        "water_source": "р. Талас",
        "type": "dam",
        "provenance_id": uuid.uuid4(),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock


def _make_mock_structure(**overrides):
    """Create a mock StructureModel with sensible defaults."""
    defaults = {
        "id": uuid.uuid4(),
        "name_ru": "Плотина Талас",
        "name_kk": None,
        "name_en": "Talas Dam",
        "type": "dam",
        "district": "Жамбылский район",
        "water_source": "р. Талас",
        "geometry": None,
        "status": "active",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock


class TestMatchCandidate:
    """Tests for MatchingService.match_candidate."""

    @pytest.mark.asyncio
    async def test_no_geometry_returns_new_candidate(self):
        """Candidate with no geometry gets new_candidate match status."""
        candidate = _make_mock_candidate(geometry=None)
        service = MatchingService()
        result = await service.match_candidate(candidate)

        assert result.match_status == "new_candidate"
        assert result.confidence == "LOW"
        assert result.matched_structure_id is None

    @pytest.mark.asyncio
    async def test_no_nearby_structures_returns_new_candidate(self):
        """Candidate with geometry but no nearby structures → new_candidate."""
        candidate = _make_mock_candidate(geometry="SRID=4326;POINT(71.4 42.9)")

        # Mock async_session to return no nearby structures
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("api.services.matching_service.async_session", MagicMock(return_value=mock_cm)):
            service = MatchingService()
            result = await service.match_candidate(candidate)

        assert result.match_status == "new_candidate"
        assert result.confidence == "LOW"

    @pytest.mark.asyncio
    async def test_close_match_returns_matched(self):
        """Candidate close to structure with high name similarity → matched."""
        candidate = _make_mock_candidate(
            geometry="SRID=4326;POINT(71.4 42.9)",
            name="Плотина Талас",
            type="dam",
            district="Жамбылский район",
            water_source="р. Талас",
        )
        structure = _make_mock_structure(
            name_ru="Плотина Талас",
            type="dam",
            district="Жамбылский район",
            water_source="р. Талас",
        )

        # Mock: nearby structures found with distance 50m
        nearby_row = (structure, 50.0)

        # First call: nearby structures query
        # Subsequent calls: name similarity queries
        mock_session = MagicMock()

        nearby_result = MagicMock()
        nearby_result.all.return_value = [nearby_row]

        # For similarity queries — return high similarity
        sim_result = MagicMock()
        sim_result.scalar.return_value = 0.85

        mock_session.execute = AsyncMock(
            side_effect=[nearby_result, sim_result, sim_result, sim_result]
        )

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("api.services.matching_service.async_session", MagicMock(return_value=mock_cm)):
            service = MatchingService()
            result = await service.match_candidate(candidate)

        assert result.match_status == "matched"
        assert result.confidence == "HIGH"
        assert result.matched_structure_id == structure.id
        assert result.evidence["name_similarity"] == 0.85
        assert result.evidence["spatial_distance_m"] == 50.0

    @pytest.mark.asyncio
    async def test_moderate_match_returns_likely_match(self):
        """Candidate within 500m with moderate name similarity → likely_match."""
        candidate = _make_mock_candidate(
            geometry="SRID=4326;POINT(71.4 42.9)",
            name="Канал Шу",
            type="canal",
            district=None,
            water_source=None,
        )
        structure = _make_mock_structure(
            name_ru="Канал Шу",
            type="canal",
            district=None,
            water_source=None,
        )

        nearby_row = (structure, 300.0)  # 300m away

        nearby_result = MagicMock()
        nearby_result.all.return_value = [nearby_row]

        sim_result = MagicMock()
        sim_result.scalar.return_value = 0.5  # moderate similarity

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(
            side_effect=[nearby_result, sim_result, sim_result, sim_result]
        )

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("api.services.matching_service.async_session", MagicMock(return_value=mock_cm)):
            service = MatchingService()
            result = await service.match_candidate(candidate)

        assert result.match_status == "likely_match"
        assert result.confidence == "MEDIUM"

    @pytest.mark.asyncio
    async def test_close_but_mismatch_returns_conflict(self):
        """Candidate close spatially but name/type mismatch → conflict."""
        candidate = _make_mock_candidate(
            geometry="SRID=4326;POINT(71.4 42.9)",
            name="Совершенно другое",
            type="weir",
            district=None,
            water_source=None,
        )
        structure = _make_mock_structure(
            name_ru="Плотина Талас",
            type="dam",
            district=None,
            water_source=None,
        )

        nearby_row = (structure, 50.0)

        nearby_result = MagicMock()
        nearby_result.all.return_value = [nearby_row]

        sim_result = MagicMock()
        sim_result.scalar.return_value = 0.1  # very low similarity

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(
            side_effect=[nearby_result, sim_result, sim_result, sim_result]
        )

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("api.services.matching_service.async_session", MagicMock(return_value=mock_cm)):
            service = MatchingService()
            result = await service.match_candidate(candidate)

        assert result.match_status == "conflict"
        assert result.confidence == "LOW"


# ---------------------------------------------------------------------------
# match_all_unmatched tests
# ---------------------------------------------------------------------------


class TestMatchAllUnmatched:
    """Tests for MatchingService.match_all_unmatched batch processing."""

    @pytest.mark.asyncio
    async def test_match_all_processes_unmatched(self):
        """match_all_unmatched processes all unmatched candidates."""
        candidates = [
            _make_mock_candidate(geometry=None, name=f"Candidate {i}")
            for i in range(3)
        ]

        # Mock match_candidate to avoid complex DB interactions
        mock_results = [
            CandidateMatchResult(
                candidate_id=c.id,
                match_status="new_candidate",
                confidence="LOW",
                confidence_score=0.0,
                matched_structure_id=None,
                evidence={"reason": "no_geometry"},
            )
            for c in candidates
        ]

        with patch.object(
            MatchingService, "match_candidate",
            side_effect=mock_results,
        ), patch(
            "api.services.matching_service.async_session"
        ) as mock_async_session:
            # First call: load unmatched candidates
            load_result = MagicMock()
            load_result.scalars.return_value.all.return_value = candidates

            # Update calls for each candidate
            update_session = MagicMock()
            update_session.execute = AsyncMock(return_value=None)
            update_session.begin = MagicMock()
            update_cm = MagicMock()
            update_cm.__aenter__ = AsyncMock(return_value=update_session)
            update_cm.__aexit__ = AsyncMock(return_value=None)

            # Load session
            load_session = MagicMock()
            load_session.execute = AsyncMock(return_value=load_result)
            load_cm = MagicMock()
            load_cm.__aenter__ = AsyncMock(return_value=load_session)
            load_cm.__aexit__ = AsyncMock(return_value=None)

            mock_async_session.side_effect = [load_cm, update_cm, update_cm, update_cm]

            service = MatchingService()
            results = await service.match_all_unmatched()

        assert len(results) == 3
        assert all(r.match_status == "new_candidate" for r in results)

    @pytest.mark.asyncio
    async def test_match_all_empty(self):
        """match_all_unmatched returns empty list when no unmatched candidates."""
        load_result = MagicMock()
        load_result.scalars.return_value.all.return_value = []

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=load_result)

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "api.services.matching_service.async_session",
            MagicMock(return_value=mock_cm),
        ):
            service = MatchingService()
            results = await service.match_all_unmatched()

        assert len(results) == 0
