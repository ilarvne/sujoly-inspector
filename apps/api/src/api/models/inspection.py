"""Inspection and InspectionPhoto ORM models.

InspectionModel: Inspection record per structure — findings, condition, red_flags.
  Linked to structure via structure_id FK, with provenance tracking (DATA-07).
  Creating an inspection triggers risk recomputation (D-05 trigger #1).
InspectionPhotoModel: Photo attachments linked to inspections via MinIO object keys.
  Photos are stored in MinIO (INT-04), not in PostgreSQL.
  Only the object key reference lives here.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class InspectionModel(Base):
    """Inspection record per structure — findings, condition, red_flags.

    Creating an inspection triggers risk recomputation for that structure
    via the recompute_structure_risk Celery task (D-05 trigger #1).
    """

    __tablename__ = "inspections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("structures.id"), nullable=False, index=True
    )
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    inspector_name: Mapped[str] = mapped_column(String(255), nullable=False)
    inspector_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_at_inspection: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    condition_score_at_inspection: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    red_flags_observed: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class InspectionPhotoModel(Base):
    """Photo attachments linked to inspections via MinIO object keys (D-15).

    Photos are stored in MinIO (INT-04). Only the object key reference
    is stored in PostgreSQL. Presigned URLs are generated on-demand
    via MinIOService.presigned_download_url (T-03-14 mitigation).
    """

    __tablename__ = "inspection_photos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("inspections.id"), nullable=False, index=True
    )
    minio_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="overview"
    )
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
