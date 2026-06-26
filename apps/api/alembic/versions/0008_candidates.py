"""create candidates table with pg_trgm for name similarity

Revision ID: 0008
Revises: 0006
Create Date: 2026-06-26

Creates the candidates table per DISC-03/DISC-06:
- id (UUID PK), name (String 500), source_type (String 50), source_id (String 255)
- geometry (Point 4326) for candidate location
- match_status with CheckConstraint (unmatched/matched/likely_match/new_candidate/conflict/rejected)
- matched_structure_id FK to structures.id (nullable)
- confidence with CheckConstraint (HIGH/MEDIUM/LOW)
- confidence_score (Float 0-1)
- evidence (JSONB) for match evidence dict
- district, water_source, type (nullable strings)
- review_notes, reviewed_by, reviewed_at for review workflow
- provenance_id FK to provenance.id
- created_at, updated_at timestamps

Extensions:
- pg_trgm extension for fuzzy name matching
- trgm GiST index on name column
- spatial GiST index on geometry column
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import Float, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create candidates table with check constraints, pg_trgm, and spatial indexes."""
    # Enable pg_trgm extension for fuzzy name matching (DISC-06)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "candidates",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("name", String(500), nullable=False),
        sa.Column("source_type", String(50), nullable=False),
        sa.Column("source_id", String(255), nullable=False),
        sa.Column("geometry", Geometry("Point", srid=4326), nullable=True),
        sa.Column("match_status", String(50), nullable=False, server_default="unmatched"),
        sa.Column("matched_structure_id", Uuid, nullable=True),
        sa.Column("confidence", String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("confidence_score", Float, nullable=True),
        sa.Column("evidence", JSONB, nullable=True),
        sa.Column("district", String(255), nullable=True),
        sa.Column("water_source", String(255), nullable=True),
        sa.Column("type", String(100), nullable=True),
        sa.Column("review_notes", Text, nullable=True),
        sa.Column("reviewed_by", Uuid, nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["matched_structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
        sa.CheckConstraint(
            "source_type IN ('osm', 'satellite', 'ocr', 'manual')",
            name="ck_candidate_source_type",
        ),
        sa.CheckConstraint(
            "match_status IN ('unmatched', 'matched', 'likely_match', 'new_candidate', 'conflict', 'rejected')",
            name="ck_candidate_match_status",
        ),
        sa.CheckConstraint(
            "confidence IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_candidate_confidence",
        ),
    )
    # Index on match_status for filtering by match state
    op.create_index("ix_candidates_match_status", "candidates", ["match_status"])
    # Index on source_type for filtering by discovery source
    op.create_index("ix_candidates_source_type", "candidates", ["source_type"])
    # Spatial GiST index on geometry for proximity queries
    op.execute(
        "CREATE INDEX ix_candidates_geometry ON candidates USING GIST (geometry)"
    )
    # Trigram GiST index on name for fuzzy matching (DISC-06)
    op.execute(
        "CREATE INDEX ix_candidates_name_trgm ON candidates USING GIST (name gist_trgm_ops)"
    )


def downgrade() -> None:
    """Drop candidates table and indexes, then drop pg_trgm extension."""
    op.execute("DROP INDEX IF EXISTS ix_candidates_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_candidates_geometry")
    op.drop_index("ix_candidates_source_type", table_name="candidates")
    op.drop_index("ix_candidates_match_status", table_name="candidates")
    op.drop_table("candidates")
    # Drop pg_trgm extension — safe only if no other objects depend on it
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
