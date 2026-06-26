"""Pydantic schemas for structure CRUD and search endpoints.

Provides:
- StructureCreate: request body for POST /api/v1/structures
- StructureUpdate: request body for PUT /api/v1/structures/{id} (all Optional)
- StructureResponse: response model with ConfigDict(from_attributes=True)
- StructureListResponse: paginated list envelope (D-16)
- SearchResultResponse: StructureResponse + match_score for ranked search (D-12)
- SearchListResponse: paginated search results envelope
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StructureCreate(BaseModel):
    """Request body for creating a structure record.

    All filterable fields from D-08 are included for direct creation.
    The `type` field is required; all others are optional.
    """

    name_ru: str | None = Field(None, description="Structure name in Russian")
    name_kk: str | None = Field(None, description="Structure name in Kazakh")
    name_en: str | None = Field(None, description="Structure name in English")
    type: str = Field(..., description="Structure type: canal, dam, reservoir, etc.")
    latitude: float | None = Field(None, description="Latitude (WGS84)")
    longitude: float | None = Field(None, description="Longitude (WGS84)")
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
    latitude: float | None = None
    longitude: float | None = None
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
    SQLAlchemy ORM model instances. The `geometry` field is computed from
    latitude/longitude columns as a GeoJSON Point dict.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_ru: str | None
    name_kk: str | None
    name_en: str | None
    type: str
    latitude: float | None = None
    longitude: float | None = None
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

    @model_validator(mode="before")
    @classmethod
    def _build_geometry_from_latlon(cls, data):
        """Build GeoJSON Point geometry dict from latitude/longitude columns.

        Since we replaced PostGIS Geometry with plain Float columns, the
        geometry is constructed in Python from latitude/longitude. This
        validator runs before field validation and injects the computed
        `geometry` dict into the data.
        """
        # Handle ORM model instances (from_attributes=True)
        if hasattr(data, "latitude") and hasattr(data, "longitude"):
            lat = getattr(data, "latitude", None)
            lon = getattr(data, "longitude", None)
            if lat is not None and lon is not None:
                # Inject geometry as a dict — model_validate will pick it up
                # We can't set attribute on ORM instance, so convert to dict
                d = {}
                for field in ["id", "name_ru", "name_kk", "name_en", "type",
                              "latitude", "longitude", "district", "water_source",
                              "technical_condition", "wear_percentage",
                              "commissioning_year", "cadastral_number",
                              "structure_count", "provenance_id", "status",
                              "created_at", "updated_at"]:
                    d[field] = getattr(data, field, None)
                d["geometry"] = {"type": "Point", "coordinates": [lon, lat]}
                return d
        # Handle dict input
        if isinstance(data, dict):
            lat = data.get("latitude")
            lon = data.get("longitude")
            if lat is not None and lon is not None and "geometry" not in data:
                data["geometry"] = {"type": "Point", "coordinates": [lon, lat]}
        return data


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
