"""Provenance ORM model — immutable record of where a fact came from.

Every structure record and structure fact has a provenance_id FK to this table.
This is the core architecture principle (DATA-07): every fact has a source,
confidence, and timestamp.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class ProvenanceModel(Base):
    """Immutable record of where a fact came from.

    Fields:
    - source_type: kazvodhoz_spreadsheet, osm, satellite, ocr, manual, ai_inferred, inspection
    - source_reference: URL, file path, OSM element ID, satellite scene ID, etc.
    - confidence_level: HIGH, MEDIUM, LOW
    - contributor: Person, system, or process that contributed this fact
    - recorded_at: When this provenance was captured
    """

    __tablename__ = "provenance"
    __table_args__ = (
        CheckConstraint(
            "confidence_level IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_provenance_confidence_level",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[str] = mapped_column(
        String(10), nullable=False, default="HIGH"
    )
    contributor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
