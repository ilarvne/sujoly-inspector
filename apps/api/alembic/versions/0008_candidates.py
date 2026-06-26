"""create candidates table with pg_trgm for name similarity

Revision ID: 0008
Revises: 0006
Create Date: 2026-06-26

NEUTRALIZED: Superseded by 0010_no_postgis_clean which creates the candidates
table with plain Float lat/lon columns. This migration is a no-op.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass


def downgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass
