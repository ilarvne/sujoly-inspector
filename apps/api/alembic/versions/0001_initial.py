"""initial migration — provenance, structures, structure_facts

Revision ID: 0001
Revises:
Create Date: 2026-06-25

NEUTRALIZED: This migration originally used PostGIS Geometry types.
Migration 0010_no_postgis_clean now handles all table creation with
plain Float lat/lon columns. This migration is a no-op.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass


def downgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass
