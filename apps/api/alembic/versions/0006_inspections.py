"""create inspections and inspection_photos tables

Revision ID: 0006
Revises: 0004, 0005
Create Date: 2026-06-26

NEUTRALIZED: Superseded by 0010_no_postgis_clean. This migration is a no-op.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | tuple[str, ...] | None = ("0004", "0005")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass


def downgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass
