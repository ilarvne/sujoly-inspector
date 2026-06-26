"""add filterable columns, generated tsvector, trigram indexes, nullable geometry

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-26

NEUTRALIZED: Superseded by 0010_no_postgis_clean which creates all columns
from scratch with plain Float lat/lon. This migration is a no-op.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass


def downgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass
