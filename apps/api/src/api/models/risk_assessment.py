"""RiskAssessment ORM model — persisted risk assessments with history (D-04).

Every risk assessment is a snapshot of the computed risk factors at a point
in time. The valid_to field enables time-based history: the current assessment
has valid_to=NULL, and previous assessments have valid_to set when a new
assessment is created.

The is_override flag distinguishes system-computed assessments from
engineer overrides (D-13, RISK-06). Override assessments preserve the
system-computed values in contributing_factors for audit transparency.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class RiskAssessmentModel(Base):
    """Persisted risk assessment with full factor breakdown per D-04.

    Fields:
    - condition_score: Blended 0-100 score (0=perfect, 100=total failure) per D-06.
    - consequence_factor: Structure-type-based factor (0.5-2.0) per D-02.
    - seasonal_modifier: Flood-season urgency multiplier (0.8-1.5) per D-02.
    - staleness_modifier: Data-freshness multiplier (0.5-1.5) per D-02.
    - composite_score: condition * consequence * seasonal * staleness per D-03.
    - inspection_interval: One of emergency/30d/90d/180d/12mo/24mo per D-03.
    - repair_status: One of normal/inspection_required/repair_required/critical_condition per D-08.
    - red_flags: Triggered red-flag identifiers per D-07 (JSONB array).
    - contributing_factors: Dict of input values that fed the computation (JSONB).
    - provenance_id: FK to provenance record for this assessment (DATA-07).
    - is_override: True if this assessment was manually overridden by an engineer (D-13).
    - computed_at: When this assessment was computed.
    - valid_to: NULL if current, timestamp when superseded by a newer assessment.
    """

    __tablename__ = "risk_assessments"
    __table_args__ = (
        CheckConstraint(
            "inspection_interval IN ('emergency','30d','90d','180d','12mo','24mo')",
            name="ck_risk_interval",
        ),
        CheckConstraint(
            "repair_status IN ('normal','inspection_required','repair_required','critical_condition')",
            name="ck_risk_repair_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("structures.id"), nullable=False, index=True
    )
    condition_score: Mapped[float] = mapped_column(Float, nullable=False)
    consequence_factor: Mapped[float] = mapped_column(Float, nullable=False)
    seasonal_modifier: Mapped[float] = mapped_column(Float, nullable=False)
    staleness_modifier: Mapped[float] = mapped_column(Float, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    inspection_interval: Mapped[str] = mapped_column(String(20), nullable=False)
    repair_status: Mapped[str] = mapped_column(String(30), nullable=False)
    red_flags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    contributing_factors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    is_override: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
