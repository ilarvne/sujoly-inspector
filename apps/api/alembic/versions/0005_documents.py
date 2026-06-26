"""create documents table

Revision ID: 0005
Revises: 0003
Create Date: 2026-06-26

Creates the documents table per D-17:
- id (UUID PK)
- structure_id (UUID FK→structures.id, nullable — some docs aren't structure-specific)
- document_type (enum: passport/inspection_report/technical_spec/photo/other)
- title (String 500)
- language (enum: ru/kk/en)
- minio_bucket (String 100)
- minio_object_key (String 500)
- file_size_bytes (Integer, nullable)
- uploaded_by (String 255, nullable)
- provenance_id (UUID FK→provenance.id)
- created_at (DateTime with timezone)

CheckConstraints on document_type and language enums.
Branched from 0003 (parallel with 0004 from Plan 03-03 — both Wave 2).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Uuid

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create documents table with check constraints and indexes."""
    op.create_table(
        "documents",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("structure_id", Uuid, nullable=True),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("minio_bucket", sa.String(100), nullable=False),
        sa.Column("minio_object_key", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("uploaded_by", sa.String(255), nullable=True),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
        sa.CheckConstraint(
            "document_type IN ('passport','inspection_report','technical_spec','photo','other')",
            name="ck_documents_type",
        ),
        sa.CheckConstraint(
            "language IN ('ru','kk','en')",
            name="ck_documents_language",
        ),
    )
    op.create_index("ix_documents_structure_id", "documents", ["structure_id"])


def downgrade() -> None:
    """Drop documents table and indexes."""
    op.drop_index("ix_documents_structure_id", table_name="documents")
    op.drop_table("documents")
