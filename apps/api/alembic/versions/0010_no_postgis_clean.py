"""clean rebuild — drop all tables, recreate without PostGIS/pgvector

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-26

Drops ALL existing tables (which used PostGIS Geometry and pgvector Vector types)
and recreates the full schema using only plain PostgreSQL types:

- structures: latitude/longitude FLOAT columns instead of Geometry(Point,4326)
- candidates: latitude/longitude FLOAT columns instead of Geometry(Point,4326)
- embeddings: JSONB column for embedding vectors instead of pgvector Vector(1024)
- All other tables (provenance, users, risk_assessments, documents, inspections,
  inspection_photos, structure_facts) recreated as-is (no PostGIS types)

Extensions used:
- pg_trgm: for fuzzy name matching (trigram similarity) — available on cloud PG

NO postgis, NO pgvector, NO geometry/geography types, NO vector types.
This migration works with cloud PostgreSQL where we cannot CREATE EXTENSION postgis/vector.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Float, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop all tables and recreate with plain columns (no PostGIS/pgvector)."""

    # --- Drop ALL existing tables in dependency-safe order ---
    # Use CASCADE to handle any remaining FK/index dependencies
    op.execute("DROP TABLE IF EXISTS inspection_photos CASCADE")
    op.execute("DROP TABLE IF EXISTS inspections CASCADE")
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.execute("DROP TABLE IF EXISTS risk_assessments CASCADE")
    op.execute("DROP TABLE IF EXISTS embeddings CASCADE")
    op.execute("DROP TABLE IF EXISTS candidates CASCADE")
    op.execute("DROP TABLE IF EXISTS structure_facts CASCADE")
    op.execute("DROP TABLE IF EXISTS structures CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS provenance CASCADE")

    # Drop any leftover indexes that might persist (safe IF EXISTS)
    op.execute("DROP INDEX IF EXISTS ix_structures_geometry")
    op.execute("DROP INDEX IF EXISTS ix_candidates_geometry")
    op.execute("DROP INDEX IF EXISTS ix_candidates_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_embeddings_embedding")

    # Enable pg_trgm extension (available on cloud PG — no superuser needed if already enabled)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- Recreate provenance table ---
    op.create_table(
        "provenance",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.Text, nullable=True),
        sa.Column("confidence_level", sa.String(10), nullable=False, server_default="HIGH"),
        sa.Column("contributor", sa.String(255), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "confidence_level IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_provenance_confidence_level",
        ),
    )
    op.create_index("ix_provenance_source_type", "provenance", ["source_type"])

    # --- Recreate structures table (FLOAT lat/lon, no Geometry) ---
    op.create_table(
        "structures",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("name_ru", sa.String(500), nullable=True),
        sa.Column("name_kk", sa.String(500), nullable=True),
        sa.Column("name_en", sa.String(500), nullable=True),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("latitude", Float, nullable=True),
        sa.Column("longitude", Float, nullable=True),
        sa.Column("district", sa.String(255), nullable=True),
        sa.Column("water_source", sa.String(255), nullable=True),
        sa.Column("technical_condition", sa.String(100), nullable=True),
        sa.Column("wear_percentage", Float, nullable=True),
        sa.Column("commissioning_year", sa.Integer, nullable=True),
        sa.Column("cadastral_number", sa.String(255), nullable=True),
        sa.Column("structure_count", sa.Integer, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
    )

    # B-tree indexes on filterable columns
    op.create_index("ix_structures_district", "structures", ["district"])
    op.create_index("ix_structures_water_source", "structures", ["water_source"])
    op.create_index("ix_structures_technical_condition", "structures", ["technical_condition"])
    op.create_index("ix_structures_type", "structures", ["type"])

    # Generated tsvector columns for multilingual FTS (D-10)
    op.execute(
        """
        ALTER TABLE structures ADD COLUMN search_ts_ru tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('russian', coalesce(name_ru, '')), 'A') ||
            setweight(to_tsvector('russian', coalesce(district, '')), 'B') ||
            setweight(to_tsvector('russian', coalesce(water_source, '')), 'B') ||
            setweight(to_tsvector('russian', coalesce(technical_condition, '')), 'C')
        ) STORED
        """
    )
    op.execute(
        """
        ALTER TABLE structures ADD COLUMN search_ts_kk tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('simple', coalesce(name_kk, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(district, '')), 'B')
        ) STORED
        """
    )
    op.execute(
        """
        ALTER TABLE structures ADD COLUMN search_ts_en tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(name_en, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(district, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(water_source, '')), 'B')
        ) STORED
        """
    )

    # GIN indexes on tsvector columns
    op.execute("CREATE INDEX ix_structures_search_ts_ru ON structures USING GIN (search_ts_ru)")
    op.execute("CREATE INDEX ix_structures_search_ts_kk ON structures USING GIN (search_ts_kk)")
    op.execute("CREATE INDEX ix_structures_search_ts_en ON structures USING GIN (search_ts_en)")

    # GIN trigram indexes for fuzzy matching (pg_trgm)
    op.execute("CREATE INDEX ix_structures_name_ru_trgm ON structures USING GIN (name_ru gin_trgm_ops)")
    op.execute("CREATE INDEX ix_structures_name_kk_trgm ON structures USING GIN (name_kk gin_trgm_ops)")
    op.execute("CREATE INDEX ix_structures_name_en_trgm ON structures USING GIN (name_en gin_trgm_ops)")

    # --- Recreate structure_facts table ---
    op.create_table(
        "structure_facts",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("structure_id", Uuid, nullable=False),
        sa.Column("attribute_name", sa.String(100), nullable=False),
        sa.Column("attribute_value", JSONB, nullable=False),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
    )
    op.create_index("ix_structure_facts_structure_id", "structure_facts", ["structure_id"])

    # --- Recreate users table ---
    op.create_table(
        "users",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("api_key", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "role IN ('admin', 'engineer', 'inspector', 'viewer')",
            name="ck_users_role",
        ),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_api_key", "users", ["api_key"])

    # --- Recreate risk_assessments table ---
    op.create_table(
        "risk_assessments",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("structure_id", Uuid, nullable=False),
        sa.Column("condition_score", sa.Float, nullable=False),
        sa.Column("consequence_factor", sa.Float, nullable=False),
        sa.Column("seasonal_modifier", sa.Float, nullable=False),
        sa.Column("staleness_modifier", sa.Float, nullable=False),
        sa.Column("composite_score", sa.Float, nullable=False),
        sa.Column("inspection_interval", sa.String(20), nullable=False),
        sa.Column("repair_status", sa.String(30), nullable=False),
        sa.Column("red_flags", JSONB, nullable=False, server_default="[]"),
        sa.Column("contributing_factors", JSONB, nullable=False, server_default="{}"),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("is_override", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
        sa.CheckConstraint(
            "inspection_interval IN ('emergency','30d','90d','180d','12mo','24mo')",
            name="ck_risk_interval",
        ),
        sa.CheckConstraint(
            "repair_status IN ('normal','inspection_required','repair_required','critical_condition')",
            name="ck_risk_repair_status",
        ),
    )
    op.create_index("ix_risk_structure_id", "risk_assessments", ["structure_id"])
    op.execute(
        "CREATE INDEX ix_risk_latest ON risk_assessments (structure_id) WHERE valid_to IS NULL"
    )

    # --- Recreate documents table ---
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
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
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

    # --- Recreate inspections table ---
    op.create_table(
        "inspections",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("structure_id", Uuid, nullable=False),
        sa.Column("inspection_date", sa.Date, nullable=False),
        sa.Column("inspector_name", sa.String(255), nullable=False),
        sa.Column("inspector_role", sa.String(50), nullable=True),
        sa.Column("findings", sa.Text, nullable=True),
        sa.Column("condition_at_inspection", sa.String(100), nullable=True),
        sa.Column("condition_score_at_inspection", sa.Float, nullable=True),
        sa.Column("red_flags_observed", JSONB, nullable=False, server_default="[]"),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["structure_id"], ["structures.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
    )
    op.create_index("ix_inspections_structure_id", "inspections", ["structure_id"])

    # --- Recreate inspection_photos table ---
    op.create_table(
        "inspection_photos",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("inspection_id", Uuid, nullable=False),
        sa.Column("minio_bucket", sa.String(100), nullable=False),
        sa.Column("minio_object_key", sa.String(500), nullable=False),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("photo_type", sa.String(50), nullable=False, server_default="overview"),
        sa.Column("provenance_id", Uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"]),
        sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
    )
    op.create_index("ix_inspection_photos_inspection_id", "inspection_photos", ["inspection_id"])

    # --- Recreate candidates table (FLOAT lat/lon, no Geometry) ---
    op.create_table(
        "candidates",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("name", String(500), nullable=False),
        sa.Column("source_type", String(50), nullable=False),
        sa.Column("source_id", String(255), nullable=False),
        sa.Column("latitude", Float, nullable=True),
        sa.Column("longitude", Float, nullable=True),
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
    op.create_index("ix_candidates_match_status", "candidates", ["match_status"])
    op.create_index("ix_candidates_source_type", "candidates", ["source_type"])
    # Trigram GiST index on name for fuzzy matching (pg_trgm)
    op.execute(
        "CREATE INDEX ix_candidates_name_trgm ON candidates USING GIST (name gist_trgm_ops)"
    )

    # --- Recreate embeddings table (JSONB, no pgvector Vector) ---
    op.create_table(
        "embeddings",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("source_type", String(50), nullable=False),
        sa.Column("source_id", Uuid, nullable=False),
        sa.Column("content_text", Text, nullable=False),
        sa.Column("embedding", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_embeddings_source", "embeddings", ["source_type", "source_id"]
    )


def downgrade() -> None:
    """Drop all tables recreated by this migration."""
    op.execute("DROP TABLE IF EXISTS embeddings CASCADE")
    op.execute("DROP TABLE IF EXISTS candidates CASCADE")
    op.execute("DROP TABLE IF EXISTS inspection_photos CASCADE")
    op.execute("DROP TABLE IF EXISTS inspections CASCADE")
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.execute("DROP TABLE IF EXISTS risk_assessments CASCADE")
    op.execute("DROP TABLE IF EXISTS structure_facts CASCADE")
    op.execute("DROP TABLE IF EXISTS structures CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS provenance CASCADE")
