"""Document ORM model — metadata + MinIO object key per D-17.

Architecture separation (INT-04): document binary content lives in MinIO,
not in PostgreSQL. This table stores only metadata and the MinIO object key
for retrieval via presigned URLs.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class DocumentModel(Base):
    """Document attachment record linked to a structure.

    Fields:
    - structure_id: FK to structures.id (nullable — some docs aren't structure-specific)
    - document_type: passport, inspection_report, technical_spec, photo, other
    - title: human-readable document title
    - language: ru, kk, en (trilingual support)
    - minio_bucket: MinIO bucket name (e.g., sujoly-documents)
    - minio_object_key: object key within the bucket for presigned URL generation
    - file_size_bytes: optional file size for display/limits
    - uploaded_by: username of the uploader
    - provenance_id: FK to provenance — every document has a source (DATA-07)
    - created_at: timestamp of registration
    """

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('passport','inspection_report','technical_spec','photo','other')",
            name="ck_documents_type",
        ),
        CheckConstraint(
            "language IN ('ru','kk','en')",
            name="ck_documents_language",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("structures.id"), nullable=True, index=True
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    minio_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
