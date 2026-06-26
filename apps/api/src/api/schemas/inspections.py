"""Pydantic schemas for inspection CRUD endpoints.

Provides:
- PhotoMetadata: request body for photo attachment metadata in InspectionCreate
- InspectionCreate: request body for POST /api/v1/structures/{id}/inspections
- PhotoResponse: response model for photo with presigned download URL
- InspectionResponse: response model with photos list
- InspectionListResponse: paginated list envelope (D-16)
"""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PhotoMetadata(BaseModel):
    """Request body for photo attachment metadata.

    Photos are uploaded to MinIO first, then their object keys are
    referenced in the inspection creation request.
    """

    minio_bucket: str = Field(default="sujoly-photos", description="MinIO bucket name")
    minio_object_key: str = Field(..., description="Object key/path within the bucket")
    caption: str | None = Field(None, description="Photo caption")
    photo_type: Literal["overview", "detail", "defect"] = Field(
        default="overview", description="Photo type classification"
    )


class InspectionCreate(BaseModel):
    """Request body for creating an inspection record.

    Includes an optional photos array with metadata for each photo
    attachment. Photos are already uploaded to MinIO; only the
    object keys are stored in PostgreSQL (INT-04).
    """

    inspection_date: date = Field(..., description="Date of the inspection")
    inspector_name: str = Field(..., description="Name of the inspector")
    inspector_role: str | None = Field(None, description="Role of the inspector")
    findings: str | None = Field(None, description="Inspection findings text")
    condition_at_inspection: str | None = Field(
        None, description="Condition assessment at time of inspection"
    )
    condition_score_at_inspection: float | None = Field(
        None, description="Numeric condition score at time of inspection"
    )
    red_flags_observed: list[str] = Field(
        default_factory=list, description="List of red flags observed"
    )
    photos: list[PhotoMetadata] = Field(
        default_factory=list, description="Photo attachments metadata"
    )


class PhotoResponse(BaseModel):
    """Response model for a photo attachment with presigned download URL.

    Uses ConfigDict(from_attributes=True) to enable model_validate() from
    InspectionPhotoModel ORM instances. The presigned_download_url is
    generated on-demand (not stored in DB) — T-03-14 mitigation.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    minio_bucket: str
    minio_object_key: str
    caption: str | None
    photo_type: str
    presigned_download_url: str | None = None


class InspectionResponse(BaseModel):
    """Response model for an inspection record with photos list.

    Uses ConfigDict(from_attributes=True) to enable model_validate() from
    InspectionModel ORM instances.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    structure_id: uuid.UUID
    inspection_date: date
    inspector_name: str
    inspector_role: str | None
    findings: str | None
    condition_at_inspection: str | None
    condition_score_at_inspection: float | None
    red_flags_observed: list
    provenance_id: uuid.UUID
    created_at: datetime
    photos: list[PhotoResponse] = Field(default_factory=list)


class InspectionListResponse(BaseModel):
    """Paginated list response with total count (D-16).

    The pagination envelope provides `total` for frontend pagination UI.
    """

    items: list[InspectionResponse]
    total: int
    offset: int
    limit: int
