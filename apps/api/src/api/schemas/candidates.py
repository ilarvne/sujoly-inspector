"""Pydantic schemas for candidate CRUD, review, and match result endpoints.

Provides:
- CandidateCreate: request body for POST /api/v1/candidates
- CandidateResponse: response model with ConfigDict(from_attributes=True)
- CandidateListResponse: paginated list envelope
- CandidateReviewRequest: request body for review/patch endpoints
- CandidateMatchResult: for matching engine output — candidate_id, match_status,
  confidence, confidence_score, matched_structure_id, evidence
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CandidateCreate(BaseModel):
    """Request body for creating a candidate record from a discovery source.

    The `source_type`, `source_id`, and `name` fields are required.
    Geometry is provided as lat/lng; the service layer converts to WKT.
    """

    source_type: str = Field(
        ..., description="Discovery source: osm, satellite, ocr, manual"
    )
    source_id: str = Field(
        ..., description="External reference: OSM node/way ID, satellite scene ID, etc."
    )
    name: str = Field(..., description="Candidate name from source")
    latitude: float | None = Field(None, description="Latitude for geometry Point")
    longitude: float | None = Field(None, description="Longitude for geometry Point")
    evidence: dict | None = Field(
        None, description="Evidence sources and contributions"
    )
    district: str | None = Field(None, description="Administrative district")
    water_source: str | None = Field(None, description="Water source name")
    type: str | None = Field(None, description="Inferred structure type")


class CandidateResponse(BaseModel):
    """Response model for a candidate record.

    Uses ConfigDict(from_attributes=True) to enable model_validate() from
    SQLAlchemy ORM model instances.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    source_type: str
    source_id: str
    geometry: dict | None = None
    match_status: str
    matched_structure_id: uuid.UUID | None = None
    confidence: str
    confidence_score: float | None = None
    evidence: dict | None = None
    district: str | None = None
    water_source: str | None = None
    type: str | None = None
    review_notes: str | None = None
    reviewed_by: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    provenance_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CandidateListResponse(BaseModel):
    """Paginated list response with total count."""

    items: list[CandidateResponse]
    total: int
    offset: int
    limit: int


class CandidateReviewRequest(BaseModel):
    """Request body for reviewing a candidate — engineer review workflow.

    match_status and review_notes are the primary review fields.
    matched_structure_id is set when the engineer links the candidate to
    an existing structure.
    """

    match_status: str = Field(
        ..., description="Review decision: matched, likely_match, new_candidate, conflict, rejected"
    )
    matched_structure_id: uuid.UUID | None = Field(
        None, description="UUID of matched structure (required when match_status=matched)"
    )
    review_notes: str | None = Field(
        None, description="Engineer's review notes"
    )


class CandidateMatchResult(BaseModel):
    """Output from the matching engine — assigned match state and evidence.

    Used by the matching service to update candidate records after
    automated matching analysis.
    """

    candidate_id: uuid.UUID
    match_status: str = Field(
        ..., description="Assigned match status from matching engine"
    )
    confidence: str = Field(
        ..., description="Overall confidence: HIGH, MEDIUM, LOW"
    )
    confidence_score: float = Field(
        ..., description="Numeric confidence score 0.0-1.0"
    )
    matched_structure_id: uuid.UUID | None = Field(
        None, description="Matched structure UUID if found"
    )
    evidence: dict = Field(
        ..., description="Match evidence: similarity scores, distance, attribute comparison"
    )
