"""create risk_assessments table

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-26

Creates the risk_assessments table per D-04:
- All risk factor fields (condition_score, consequence_factor, seasonal_modifier, staleness_modifier, composite_score)
- inspection_interval and repair_status with CheckConstraints (D-03, D-08)
- red_flags and contributing_factors as JSONB for explainability
- provenance_id FK for audit trail (DATA-07)
- is_override flag for engineer overrides (D-13)
- valid_to for time-based history (same pattern as structure_facts)
- Partial index on (structure_id) WHERE valid_to IS NULL for fast latest-assessment queries
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create risk_assessments table with check constraints and indexes."""
    op.create_table(
        "risk_assessments",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("structure_id", Uuid, nullable=False),
        sa.Column("condition_score", sa.Float, nullable=False),
        sa.Column("consequence_factor", sa.Float, nullable=False),
        sa.Column("seasonal_modifier", sa.Float, nullable=False),
        sa.Column("staleness_modifier", sa.Float, nullable=False),
        sa.Column("composite_score", sa.Float, nullable=False),
        sa.Column("inspection_interval", sa.String(20), nullable=False),
        sa.Column("repair_status", sa.String(30), nullable=False),
        sa.Column("red_flags", JSONB, nullable=False, server_default="[]"),
        sa.Column("contributing_factors", JSONB, nullable=False, server_default="{}"),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("is_override", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
        sa.CheckConstraint(
            "inspection_interval IN ('emergency','30d','90d','180d','12mo','24mo')",
            name="ck_risk_interval",
        ),
        sa.CheckConstraint(
            "repair_status IN ('normal','inspection_required','repair_required','critical_condition')",
            name="ck_risk_repair_status",
        ),
    )
    # Index on structure_id for lookups
    op.create_index("ix_risk_structure_id", "risk_assessments", ["structure_id"])
    # Partial index for latest assessment queries (valid_to IS NULL)
    op.execute(
        "CREATE INDEX ix_risk_latest ON risk_assessments (structure_id) WHERE valid_to IS NULL"
    )


def downgrade() -> None:
    """Drop risk_assessments table and indexes."""
    op.execute("DROP INDEX IF EXISTS ix_risk_latest")
    op.drop_index("ix_risk_structure_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
