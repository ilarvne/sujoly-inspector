"""create documents table

Revision ID: 0005
Revises: 0003
Create Date: 2026-06-26

NEUTRALIZED: Superseded by 0010_no_postgis_clean. This migration is a no-op.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass


def downgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass
