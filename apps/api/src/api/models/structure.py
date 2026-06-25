"""Structure and StructureFact ORM models.

StructureModel: Canonical structure record — one per hydraulic structure.
  Geometry stored as PostGIS Geometry(Point, srid=4326) — no binary in PostgreSQL.
StructureFactModel: Time-based facts about a structure with provenance.
  Every attribute (condition, capacity, length, etc.) is a separate fact
  with its own provenance and time validity range.

Architecture separation (INT-04): structures in PostGIS, binary assets in MinIO.
"""

import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, String, Uuid
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
    geometry = mapped_column(Geometry("Point", srid=4326), nullable=False)
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
