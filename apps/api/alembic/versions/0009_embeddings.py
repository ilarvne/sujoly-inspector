"""create embeddings table with pgvector HNSW index

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-26

Creates the embeddings table per AI-03:
- id (UUID PK), source_type (String 50), source_id (UUID)
- content_text (Text), embedding (Vector 1536), created_at (DateTime timezone)
- Index on (source_type, source_id) for source lookup
- HNSW index on embedding column with vector_cosine_ops for fast similarity search

Extensions:
- vector extension for pgvector Vector column type
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import String, Text, Uuid

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create embeddings table with pgvector extension and HNSW index."""
    # Enable pgvector extension for vector column type (AI-03)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "embeddings",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("source_type", String(50), nullable=False),
        sa.Column("source_id", Uuid, nullable=False),
        sa.Column("content_text", Text, nullable=False),
        sa.Column("embedding", sa.Text, nullable=True),  # pgvector managed via raw SQL below
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Composite index on source_type + source_id for source lookup
    op.create_index(
        "ix_embeddings_source", "embeddings", ["source_type", "source_id"]
    )

    # Alter embedding column to pgvector Vector(1536) type
    # Using raw SQL since Alembic doesn't natively support pgvector DDL
    op.execute("ALTER TABLE embeddings ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")

    # HNSW index on embedding for fast cosine similarity search (AI-03)
    op.execute(
        "CREATE INDEX ix_embeddings_embedding ON embeddings USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Drop embeddings table, indexes, and vector extension."""
    op.execute("DROP INDEX IF EXISTS ix_embeddings_embedding")
    op.drop_index("ix_embeddings_source", table_name="embeddings")
    op.drop_table("embeddings")
    # Drop vector extension — safe only if no other objects depend on it
    op.execute("DROP EXTENSION IF EXISTS vector")
