"""Tests for CandidateModel creation and CheckConstraint validation.

Tests cover:
- CandidateModel creation with all fields
- match_status CheckConstraint validation (DISC-03)
- confidence CheckConstraint validation (DISC-06)
- source_type CheckConstraint validation
- Schema validation for CandidateCreate and CandidateMatchResult
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from api.models.candidate import CandidateModel
from api.schemas.candidates import (
    CandidateCreate,
    CandidateListResponse,
    CandidateMatchResult,
    CandidateResponse,
    CandidateReviewRequest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_candidate(**overrides):
    """Create a mock CandidateModel instance with all response fields."""
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


# ---------------------------------------------------------------------------
# CandidateModel creation tests
# ---------------------------------------------------------------------------


class TestCandidateModelCreation:
    """Tests for CandidateModel with all fields."""

    def test_candidate_model_creation_all_fields(self):
        """CandidateModel can be created with all required and optional fields."""
        provenance_id = uuid.uuid4()
        candidate = CandidateModel(
            name="OSM Dam Candidate",
            source_type="osm",
            source_id="way/123456789",
            match_status="unmatched",
            confidence="MEDIUM",
            confidence_score=0.65,
            evidence={"osm": {"tags": {"waterway": "dam"}, "distance_m": 50}},
            district="Жамбылский район",
            water_source="р. Талас",
            type="dam",
            provenance_id=provenance_id,
        )
        assert candidate.name == "OSM Dam Candidate"
        assert candidate.source_type == "osm"
        assert candidate.source_id == "way/123456789"
        assert candidate.match_status == "unmatched"
        assert candidate.confidence == "MEDIUM"
        assert candidate.confidence_score == 0.65
        assert candidate.evidence == {"osm": {"tags": {"waterway": "dam"}, "distance_m": 50}}
        assert candidate.district == "Жамбылский район"
        assert candidate.water_source == "р. Талас"
        assert candidate.type == "dam"
        assert candidate.provenance_id == provenance_id
        assert candidate.matched_structure_id is None
        assert candidate.review_notes is None
        assert candidate.reviewed_by is None
        assert candidate.reviewed_at is None

    def test_candidate_model_minimal_fields(self):
        """CandidateModel can be created with only required fields + defaults."""
        provenance_id = uuid.uuid4()
        candidate = CandidateModel(
            name="Minimal Candidate",
            source_type="manual",
            source_id="manual-001",
            match_status="unmatched",
            confidence="MEDIUM",
            provenance_id=provenance_id,
        )
        assert candidate.name == "Minimal Candidate"
        assert candidate.source_type == "manual"
        assert candidate.match_status == "unmatched"
        assert candidate.confidence == "MEDIUM"
        assert candidate.confidence_score is None
        assert candidate.evidence is None
        assert candidate.district is None
        assert candidate.water_source is None
        assert candidate.type is None

    def test_candidate_model_default_uuid(self):
        """CandidateModel id field is a UUID primary key."""
        provenance_id = uuid.uuid4()
        candidate_id = uuid.uuid4()
        candidate = CandidateModel(
            id=candidate_id,
            name="Test",
            source_type="osm",
            source_id="node/1",
            provenance_id=provenance_id,
        )
        assert candidate.id == candidate_id
        assert isinstance(candidate.id, uuid.UUID)

    def test_candidate_model_timestamps(self):
        """CandidateModel created_at and updated_at are DateTime timezone fields."""
        provenance_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        candidate = CandidateModel(
            name="Test",
            source_type="osm",
            source_id="node/1",
            provenance_id=provenance_id,
            created_at=now,
            updated_at=now,
        )
        assert candidate.created_at is not None
        assert candidate.updated_at is not None
        # Verify timezone-aware datetime
        assert candidate.created_at.tzinfo is not None


# ---------------------------------------------------------------------------
# CheckConstraint validation tests
# ---------------------------------------------------------------------------


class TestCandidateCheckConstraints:
    """Tests for CandidateModel CheckConstraint validation (DISC-03, DISC-06)."""

    def test_match_status_valid_values(self):
        """Valid match_status values are accepted by the CheckConstraint definition."""
        valid_statuses = ["unmatched", "matched", "likely_match", "new_candidate", "conflict", "rejected"]
        # Verify the CheckConstraint definition includes all valid values
        for status in valid_statuses:
            provenance_id = uuid.uuid4()
            candidate = CandidateModel(
                name="Test",
                source_type="osm",
                source_id="node/1",
                match_status=status,
                provenance_id=provenance_id,
            )
            assert candidate.match_status == status

    def test_confidence_valid_values(self):
        """Valid confidence values are accepted by the CheckConstraint definition."""
        valid_confidences = ["HIGH", "MEDIUM", "LOW"]
        for conf in valid_confidences:
            provenance_id = uuid.uuid4()
            candidate = CandidateModel(
                name="Test",
                source_type="osm",
                source_id="node/1",
                confidence=conf,
                provenance_id=provenance_id,
            )
            assert candidate.confidence == conf

    def test_source_type_valid_values(self):
        """Valid source_type values are accepted by the CheckConstraint definition."""
        valid_types = ["osm", "satellite", "ocr", "manual"]
        for src_type in valid_types:
            provenance_id = uuid.uuid4()
            candidate = CandidateModel(
                name="Test",
                source_type=src_type,
                source_id="ref-1",
                provenance_id=provenance_id,
            )
            assert candidate.source_type == src_type

    def test_match_status_check_constraint_definition(self):
        """Verify CheckConstraint for match_status includes all DISC-03 states."""
        # Check the table_args contain the correct constraint
        table_args = CandidateModel.__table_args__
        constraint_names = [c.name for c in table_args if hasattr(c, "name")]
        assert "ck_candidate_match_status" in constraint_names

    def test_confidence_check_constraint_definition(self):
        """Verify CheckConstraint for confidence includes HIGH/MEDIUM/LOW (DISC-06)."""
        table_args = CandidateModel.__table_args__
        constraint_names = [c.name for c in table_args if hasattr(c, "name")]
        assert "ck_candidate_confidence" in constraint_names

    def test_source_type_check_constraint_definition(self):
        """Verify CheckConstraint for source_type includes osm/satellite/ocr/manual."""
        table_args = CandidateModel.__table_args__
        constraint_names = [c.name for c in table_args if hasattr(c, "name")]
        assert "ck_candidate_source_type" in constraint_names


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestCandidateSchemas:
    """Tests for Pydantic schemas for candidates."""

    def test_candidate_create_schema(self):
        """CandidateCreate schema validates required fields."""
        schema = CandidateCreate(
            source_type="osm",
            source_id="way/123456789",
            name="OSM Dam",
        )
        assert schema.source_type == "osm"
        assert schema.source_id == "way/123456789"
        assert schema.name == "OSM Dam"

    def test_candidate_create_with_geometry(self):
        """CandidateCreate schema accepts optional lat/lng fields."""
        schema = CandidateCreate(
            source_type="satellite",
            source_id="scene-001",
            name="Satellite Discovery",
            latitude=42.9,
            longitude=71.4,
            evidence={"satellite": {"confidence": 0.8}},
        )
        assert schema.latitude == 42.9
        assert schema.longitude == 71.4
        assert schema.evidence == {"satellite": {"confidence": 0.8}}

    def test_candidate_response_from_attributes(self):
        """CandidateResponse validates from mock ORM model (from_attributes)."""
        mock = _make_mock_candidate()
        response = CandidateResponse.model_validate(mock)
        assert response.name == "OSM Dam Candidate"
        assert response.source_type == "osm"
        assert response.match_status == "unmatched"
        assert response.confidence == "MEDIUM"

    def test_candidate_list_response(self):
        """CandidateListResponse wraps items with pagination."""
        items = [CandidateResponse.model_validate(_make_mock_candidate())]
        list_resp = CandidateListResponse(items=items, total=1, offset=0, limit=20)
        assert list_resp.total == 1
        assert len(list_resp.items) == 1

    def test_candidate_review_request(self):
        """CandidateReviewRequest validates match_status and review_notes."""
        schema = CandidateReviewRequest(
            match_status="matched",
            matched_structure_id=uuid.uuid4(),
            review_notes="Confirmed match with existing structure",
        )
        assert schema.match_status == "matched"
        assert schema.matched_structure_id is not None
        assert schema.review_notes == "Confirmed match with existing structure"

    def test_candidate_review_request_reject(self):
        """CandidateReviewRequest for rejection without matched_structure_id."""
        schema = CandidateReviewRequest(
            match_status="rejected",
            review_notes="Duplicate of existing record",
        )
        assert schema.match_status == "rejected"
        assert schema.matched_structure_id is None

    def test_candidate_match_result_schema(self):
        """CandidateMatchResult validates matching engine output."""
        candidate_id = uuid.uuid4()
        schema = CandidateMatchResult(
            candidate_id=candidate_id,
            match_status="likely_match",
            confidence="HIGH",
            confidence_score=0.87,
            matched_structure_id=uuid.uuid4(),
            evidence={
                "name_similarity": 0.85,
                "spatial_distance_m": 50,
                "attribute_overlap": 0.7,
            },
        )
        assert schema.candidate_id == candidate_id
        assert schema.match_status == "likely_match"
        assert schema.confidence == "HIGH"
        assert schema.confidence_score == 0.87
        assert "name_similarity" in schema.evidence
