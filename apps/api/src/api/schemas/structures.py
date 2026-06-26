"""Pydantic schemas for structure CRUD and search endpoints.

Provides:
- StructureCreate: request body for POST /api/v1/structures
- StructureUpdate: request body for PUT /api/v1/structures/{id} (all Optional)
- StructureResponse: response model with ConfigDict(from_attributes=True)
- StructureListResponse: paginated list envelope (D-16)
- SearchResultResponse: StructureResponse + match_score for ranked search (D-12)
- SearchListResponse: paginated search results envelope
"""

import struct
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StructureCreate(BaseModel):
    """Request body for creating a structure record.

    All filterable fields from D-08 are included for direct creation.
    The `type` field is required; all others are optional.
    """

    name_ru: str | None = Field(None, description="Structure name in Russian")
    name_kk: str | None = Field(None, description="Structure name in Kazakh")
    name_en: str | None = Field(None, description="Structure name in English")
    type: str = Field(..., description="Structure type: canal, dam, reservoir, etc.")
    district: str | None = Field(None, description="Administrative district (D-08)")
    water_source: str | None = Field(None, description="Water source name (D-08)")
    technical_condition: str | None = Field(
        None, description="Technical condition assessment (D-08)"
    )
    wear_percentage: float | None = Field(
        None, description="Wear percentage 0-100 (D-08)"
    )
    commissioning_year: int | None = Field(
        None, description="Year the structure was commissioned (D-08)"
    )
    cadastral_number: str | None = Field(
        None, description="Cadastral number (D-08)"
    )
    structure_count: int | None = Field(
        None, description="Number of structures at this location (D-08)"
    )


class StructureUpdate(BaseModel):
    """Request body for updating a structure record.

    Same fields as StructureCreate but ALL are Optional (including type).
    Only non-None fields are updated; the update creates a new provenance
    record and new structure_facts per D-13.
    """

    name_ru: str | None = None
    name_kk: str | None = None
    name_en: str | None = None
    type: str | None = None
    district: str | None = None
    water_source: str | None = None
    technical_condition: str | None = None
    wear_percentage: float | None = None
    commissioning_year: int | None = None
    cadastral_number: str | None = None
    structure_count: int | None = None


class StructureResponse(BaseModel):
    """Response model for a structure record.

    Uses ConfigDict(from_attributes=True) to enable model_validate() from
    SQLAlchemy ORM model instances.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_ru: str | None
    name_kk: str | None
    name_en: str | None
    type: str
    district: str | None
    water_source: str | None
    technical_condition: str | None
    wear_percentage: float | None
    commissioning_year: int | None
    cadastral_number: str | None
    structure_count: int | None
    geometry: dict | None = None
    provenance_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("geometry", mode="before")
    @classmethod
    def convert_wkb_geometry(cls, v):
        """Convert GeoAlchemy2 WKBElement to GeoJSON dict (Rule 3 fix).

        PostGIS geometry columns load as ``WKBElement`` (raw EWKB bytes) when
        accessed via SQLAlchemy ORM. Pydantic cannot serialise ``WKBElement``
        to ``dict`` directly, causing a validation error on every list/detail
        endpoint. This validator parses the EWKB binary to a GeoJSON dict for
        Point geometries (the only geometry type used in this project) without
        requiring the ``shapely`` dependency.
        """
        if v is None or isinstance(v, dict):
            return v

        # WKBElement from GeoAlchemy2 — parse EWKB to GeoJSON dict
        if hasattr(v, "data"):
            data = v.data
            if isinstance(data, str):
                data = bytes.fromhex(data)
            if not data or len(data) < 5:
                return None
            endian = "<" if data[0] == 1 else ">"
            geom_type = struct.unpack_from(endian + "I", data, 1)[0]
            has_srid = bool(geom_type & 0x20000000)
            base_type = (geom_type & 0x0FFFFFFF) % 1000
            offset = 5 + (4 if has_srid else 0)
            if base_type == 1:  # Point
                if len(data) < offset + 16:
                    return None
                x = struct.unpack_from(endian + "d", data, offset)[0]
                y = struct.unpack_from(endian + "d", data, offset + 8)[0]
                return {"type": "Point", "coordinates": [x, y]}
        return None


class StructureListResponse(BaseModel):
    """Paginated list response with total count (D-16).

    The pagination envelope provides `total` for frontend pagination UI.
    """

    items: list[StructureResponse]
    total: int
    offset: int
    limit: int


class SearchResultResponse(StructureResponse):
    """Search result with match score for ranked search (D-12).

    Extends StructureResponse with a match_score field that represents
    the blended FTS + trigram similarity score.
    """

    match_score: float = 0.0


class SearchListResponse(BaseModel):
    """Paginated search results envelope."""

    items: list[SearchResultResponse]
    total: int
    offset: int
    limit: int
