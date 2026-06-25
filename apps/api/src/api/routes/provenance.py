"""Provenance REST endpoints.

Provides:
- POST /api/v1/provenance: create a provenance record (201)
- GET /api/v1/provenance/{provenance_id}: retrieve by UUID (200 or 404)
- GET /api/v1/provenance: query with optional filters (200, list)

DATA-07: provenance is queryable by source_type, confidence_level, and timestamp.
"""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from api.services.provenance_service import (
    create_provenance,
    get_provenance,
    query_provenance,
)

router = APIRouter(prefix="/api/v1", tags=["provenance"])


class ProvenanceCreate(BaseModel):
    """Request body for creating a provenance record."""

    source_type: str = Field(
        ...,
        description=(
            "Source type: kazvodhoz_spreadsheet, osm, satellite, ocr, "
            "manual, ai_inferred, inspection"
        ),
    )
    source_reference: str | None = Field(
        None, description="URL, file path, OSM element ID, satellite scene ID, etc."
    )
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        "HIGH", description="Confidence level of the source"
    )
    contributor: str | None = Field(
        None, description="Person, system, or process that contributed this fact"
    )


class ProvenanceResponse(BaseModel):
    """Response model for a provenance record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: str
    source_reference: str | None
    confidence_level: str
    contributor: str | None
    recorded_at: datetime


@router.post(
    "/provenance",
    response_model=ProvenanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_provenance_endpoint(body: ProvenanceCreate) -> ProvenanceResponse:
    """Create a new provenance record."""
    model = await create_provenance(
        source_type=body.source_type,
        confidence_level=body.confidence_level,
        source_reference=body.source_reference,
        contributor=body.contributor,
    )
    return ProvenanceResponse.model_validate(model)


@router.get(
    "/provenance/{provenance_id}",
    response_model=ProvenanceResponse,
)
async def get_provenance_endpoint(provenance_id: uuid.UUID) -> ProvenanceResponse:
    """Retrieve a provenance record by ID."""
    model = await get_provenance(provenance_id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provenance record '{provenance_id}' not found",
        )
    return ProvenanceResponse.model_validate(model)


@router.get("/provenance", response_model=list[ProvenanceResponse])
async def list_provenance_endpoint(
    source_type: str | None = None,
    confidence_level: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[ProvenanceResponse]:
    """Query provenance records with optional filters.

    Filters:
    - source_type: e.g., 'kazvodhoz_spreadsheet'
    - confidence_level: HIGH, MEDIUM, LOW
    - offset/limit: pagination
    """
    models = await query_provenance(
        source_type=source_type,
        confidence_level=confidence_level,
        offset=offset,
        limit=limit,
    )
    return [ProvenanceResponse.model_validate(m) for m in models]
