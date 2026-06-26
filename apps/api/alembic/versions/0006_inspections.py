"""create inspections and inspection_photos tables

Revision ID: 0006
Revises: 0004, 0005
Create Date: 2026-06-26

Merge migration joining branches 0004 (risk_assessments from Plan 03-03)
and 0005 (documents from Plan 03-04). Creates two tables per D-14/D-15:

Table `inspections` (D-14):
- id (UUID PK)
- structure_id (UUID FK→structures.id, nullable=False, indexed)
- inspection_date (Date, nullable=False)
- inspector_name (String 255, nullable=False)
- inspector_role (String 50, nullable=True)
- findings (Text, nullable=True)
- condition_at_inspection (String 100, nullable=True)
- condition_score_at_inspection (Float, nullable=True)
- red_flags_observed (JSONB, nullable=False, default=[])
- provenance_id (UUID FK→provenance.id, nullable=False)
- created_at (DateTime with timezone)

Table `inspection_photos` (D-15):
- id (UUID PK)
- inspection_id (UUID FK→inspections.id, nullable=False, indexed)
- minio_bucket (String 100, nullable=False)
- minio_object_key (String 500, nullable=False)
- caption (Text, nullable=True)
- photo_type (String 50, nullable=False, default='overview')
- provenance_id (UUID FK→provenance.id, nullable=False)
- created_at (DateTime with timezone)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | tuple[str, ...] | None = ("0004", "0005")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create inspections and inspection_photos tables."""
    op.create_table(
        "inspections",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("structure_id", Uuid, nullable=False),
        sa.Column("inspection_date", sa.Date, nullable=False),
        sa.Column("inspector_name", sa.String(255), nullable=False),
        sa.Column("inspector_role", sa.String(50), nullable=True),
        sa.Column("findings", sa.Text, nullable=True),
        sa.Column("condition_at_inspection", sa.String(100), nullable=True),
        sa.Column("condition_score_at_inspection", sa.Float, nullable=True),
        sa.Column("red_flags_observed", JSONB, nullable=False, server_default="[]"),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
    )
    op.create_index("ix_inspections_structure_id", "inspections", ["structure_id"])

    op.create_table(
        "inspection_photos",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("inspection_id", Uuid, nullable=False),
        sa.Column("minio_bucket", sa.String(100), nullable=False),
        sa.Column("minio_object_key", sa.String(500), nullable=False),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("photo_type", sa.String(50), nullable=False, server_default="overview"),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
    )
    op.create_index("ix_inspection_photos_inspection_id", "inspection_photos", ["inspection_id"])


def downgrade() -> None:
    """Drop inspection_photos and inspections tables (reverse order)."""
    op.drop_index("ix_inspection_photos_inspection_id", table_name="inspection_photos")
    op.drop_table("inspection_photos")
    op.drop_index("ix_inspections_structure_id", table_name="inspections")
    op.drop_table("inspections")
