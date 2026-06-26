"""Structure and StructureFact ORM models.

StructureModel: Canonical structure record — one per hydraulic structure.
  Geometry stored as PostGIS Geometry(Point, srid=4326) — no binary in PostgreSQL.
StructureFactModel: Time-based facts about a structure with provenance.
  Every attribute (condition, capacity, length, etc.) is a separate fact
  with its own provenance and time validity range.

Architecture separation (INT-04): structures in PostGIS, binary assets in MinIO.
"""

import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class StructureModel(Base):
    """Canonical structure record — one per hydraulic structure.

    Binary assets (imagery, documents, photos) are stored in MinIO, not here.
    PostGIS stores only the vector feature (geometry point) and metadata.
    """

    __tablename__ = "structures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name_ru: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name_kk: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    # D-02: geometry nullable — spreadsheet has no coordinates, assigned in Phase 4
    geometry = mapped_column(Geometry("Point", srid=4326), nullable=True)
    # D-08: filterable denormalized columns for indexed filtering
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    water_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    technical_condition: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wear_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    commissioning_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cadastral_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    structure_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # D-13: status column for soft-delete support
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    # NOTE: search_ts_ru/kk/en are GENERATED tsvector columns managed by PostgreSQL
    # via Alembic migration 0002 — NOT declared as ORM Mapped types (PATTERNS.md line 146).
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class StructureFactModel(Base):
    """Time-based facts about a structure with provenance.

    Every attribute (condition, capacity_m3s, length_km, wear_percent, etc.)
    is a separate fact with its own provenance_id and time validity range.
    valid_to=NULL means currently valid.
    """

    __tablename__ = "structure_facts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("structures.id"), nullable=False, index=True
    )
    attribute_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attribute_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
