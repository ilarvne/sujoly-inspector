"""create embeddings table with pgvector HNSW index

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-26

NEUTRALIZED: Superseded by 0010_no_postgis_clean which creates the embeddings
table with a JSONB column (no pgvector). This migration is a no-op.
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass


def downgrade() -> None:
    """No-op — superseded by 0010_no_postgis_clean."""
    pass
