"""initial migration — provenance, structures, structure_facts

Revision ID: 0001
Revises:
Create Date: 2026-06-25

Creates the core schema for provenance tracking (DATA-07) and architecture
separation (INT-04):
- provenance: immutable source records with confidence_level check constraint
- structures: canonical structure records with PostGIS Geometry(Point, srid=4326)
- structure_facts: time-based facts with JSONB attribute values, each with
  its own provenance_id FK

No binary columns in PostgreSQL — binary assets live in MinIO (INT-04).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create provenance, structures, and structure_facts tables."""
    # --- provenance table ---
    op.create_table(
        "provenance",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.Text, nullable=True),
        sa.Column("confidence_level", sa.String(10), nullable=False, server_default="HIGH"),
        sa.Column("contributor", sa.String(255), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "confidence_level IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_provenance_confidence_level",
        ),
    )
    op.create_index("ix_provenance_source_type", "provenance", ["source_type"])

    # --- structures table ---
    op.create_table(
        "structures",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("name_ru", sa.String(500), nullable=True),
        sa.Column("name_kk", sa.String(500), nullable=True),
        sa.Column("name_en", sa.String(500), nullable=True),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("geometry", Geometry("Point", srid=4326), nullable=False),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
    )
    # GiST spatial index on geometry column (PostGIS requirement)
    op.execute(
        "CREATE INDEX ix_structures_geometry ON structures USING GIST (geometry)"
    )

    # --- structure_facts table ---
    op.create_table(
        "structure_facts",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("structure_id", Uuid, nullable=False),
        sa.Column("attribute_name", sa.String(100), nullable=False),
        sa.Column("attribute_value", JSONB, nullable=False),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
    )
    op.create_index("ix_structure_facts_structure_id", "structure_facts", ["structure_id"])


def downgrade() -> None:
    """Drop tables in reverse dependency order."""
    op.drop_index("ix_structure_facts_structure_id", table_name="structure_facts")
    op.drop_table("structure_facts")

    op.execute("DROP INDEX IF EXISTS ix_structures_geometry")
    op.drop_table("structures")

    op.drop_index("ix_provenance_source_type", table_name="provenance")
    op.drop_table("provenance")
