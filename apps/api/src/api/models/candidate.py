"""CandidateModel ORM model — discovered hydraulic structure candidates.

Candidates are structures found from external sources (OSM, satellite, OCR)
that need to be compared against the existing registry. The model supports
the four-state matching workflow (DISC-03) and confidence levels (DISC-06).

Fields:
- source_type: osm, satellite, ocr, manual — where the candidate came from
- match_status: unmatched, matched, likely_match, new_candidate, conflict, rejected
- confidence: HIGH, MEDIUM, LOW — overall confidence in the match
- confidence_score: 0.0-1.0 numeric score for ranking
- evidence: JSONB dict of evidence sources and their contributions
- matched_structure_id: FK to structures.id when matched/linked
- provenance_id: FK to provenance.id for audit trail (DATA-07)
"""

import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class CandidateModel(Base):
    """Discovered hydraulic structure candidate with matching state.

    Supports the discovery pipeline:
    1. Candidates arrive from OSM, satellite analysis, or OCR
    2. Matching engine assigns match_status and confidence
    3. Engineers review and approve/reject matches
    4. Matched candidates are linked to existing structures via FK
    """

    __tablename__ = "candidates"

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('osm', 'satellite', 'ocr', 'manual')",
            name="ck_candidate_source_type",
        ),
        CheckConstraint(
            "match_status IN ('unmatched', 'matched', 'likely_match', 'new_candidate', 'conflict', 'rejected')",
            name="ck_candidate_match_status",
        ),
        CheckConstraint(
            "confidence IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_candidate_confidence",
        ),
        Index("ix_candidates_match_status", "match_status"),
        Index("ix_candidates_source_type", "source_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    geometry = mapped_column(Geometry("Point", srid=4326), nullable=True)
    match_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=lambda: "unmatched"
    )
    matched_structure_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("structures.id"), nullable=True
    )
    confidence: Mapped[str] = mapped_column(
        String(10), nullable=False, default=lambda: "MEDIUM"
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    water_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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
