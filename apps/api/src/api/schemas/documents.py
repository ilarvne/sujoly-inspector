"""Pydantic schemas for document attachment endpoints.

Provides:
- DocumentCreate: request body for POST /api/v1/structures/{id}/documents
- DocumentResponse: response model with ConfigDict(from_attributes=True)
- DocumentListResponse: list envelope with total count (D-18)

T-03-13 mitigation: Literal enum fields for document_type and language
prevent mass assignment — only whitelisted values accepted.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    """Request body for registering a document attachment.

    Client flow: get presigned upload URL → upload to MinIO → register metadata via API.
    MinIO object key is provided after the client has successfully uploaded the file.
    """

    document_type: Literal[
        "passport", "inspection_report", "technical_spec", "photo", "other"
    ] = Field(..., description="Document type per D-17")
    title: str = Field(..., description="Human-readable document title")
    language: Literal["ru", "kk", "en"] = Field(
        ..., description="Document language (trilingual support)"
    )
    minio_bucket: str = Field(
        "sujoly-documents", description="MinIO bucket name (default: sujoly-documents)"
    )
    minio_object_key: str = Field(
        ..., description="Object key within the MinIO bucket (from upload)"
    )
    file_size_bytes: int | None = Field(
        None, description="File size in bytes (optional, for display/limits)"
    )


class DocumentResponse(BaseModel):
    """Response model for a document record.

    Uses ConfigDict(from_attributes=True) to enable model_validate() from
    SQLAlchemy ORM model instances.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    structure_id: uuid.UUID | None
    document_type: str
    title: str
    language: str
    minio_bucket: str
    minio_object_key: str
    file_size_bytes: int | None
    uploaded_by: str | None
    provenance_id: uuid.UUID
    created_at: datetime
    presigned_download_url: str | None = None


class DocumentListResponse(BaseModel):
    """List response with total count (D-18)."""

    items: list[DocumentResponse]
    total: int
