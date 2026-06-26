"""add filterable columns, generated tsvector, trigram indexes, nullable geometry

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-26

Schema changes for Phase 2 data ingestion and spatial API:
- D-02: Make geometry nullable (spreadsheet has no coordinates)
- D-08: Add 7 filterable denormalized columns for indexed filtering
- D-10: Add 3 generated tsvector columns for multilingual FTS (ru/kk/en)
- D-11: Add GIN trigram indexes for fuzzy name matching (pg_trgm)
- D-13: Add status column for soft-delete support

pg_trgm extension is already enabled in docker/postgres/init-extensions.sql.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add filterable columns, generated tsvector columns, trigram indexes, nullable geometry."""

    # 1. Make geometry nullable (D-02) — use raw SQL to preserve GiST index
    #    (Pitfall #7: op.alter_column with nullable=True can drop the GiST index)
    op.execute("ALTER TABLE structures ALTER COLUMN geometry DROP NOT NULL")

    # 2. Add filterable denormalized columns (D-08)
    op.add_column("structures", sa.Column("district", sa.String(255), nullable=True))
    op.add_column("structures", sa.Column("water_source", sa.String(255), nullable=True))
    op.add_column("structures", sa.Column("technical_condition", sa.String(100), nullable=True))
    op.add_column("structures", sa.Column("wear_percentage", sa.Float, nullable=True))
    op.add_column("structures", sa.Column("commissioning_year", sa.Integer, nullable=True))
    op.add_column("structures", sa.Column("cadastral_number", sa.String(255), nullable=True))
    op.add_column("structures", sa.Column("structure_count", sa.Integer, nullable=True))

    # 3. Add status column for soft-delete support (D-13)
    op.add_column(
        "structures",
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
    )

    # 4. B-tree indexes on filterable columns
    op.create_index("ix_structures_district", "structures", ["district"])
    op.create_index("ix_structures_water_source", "structures", ["water_source"])
    op.create_index("ix_structures_technical_condition", "structures", ["technical_condition"])
    op.create_index("ix_structures_type", "structures", ["type"])

    # 5. Generated tsvector columns for multilingual FTS (D-10)
    #    Pitfall #5: Use fixed FTS config names, not column references (immutability requirement)
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

    # 6. GIN indexes on tsvector columns (D-10)
    op.execute("CREATE INDEX ix_structures_search_ts_ru ON structures USING GIN (search_ts_ru)")
    op.execute("CREATE INDEX ix_structures_search_ts_kk ON structures USING GIN (search_ts_kk)")
    op.execute("CREATE INDEX ix_structures_search_ts_en ON structures USING GIN (search_ts_en)")

    # 7. GIN trigram indexes for fuzzy matching (D-11)
    #    pg_trgm already enabled in init-extensions.sql
    op.execute("CREATE INDEX ix_structures_name_ru_trgm ON structures USING GIN (name_ru gin_trgm_ops)")
    op.execute("CREATE INDEX ix_structures_name_kk_trgm ON structures USING GIN (name_kk gin_trgm_ops)")
    op.execute("CREATE INDEX ix_structures_name_en_trgm ON structures USING GIN (name_en gin_trgm_ops)")


def downgrade() -> None:
    """Reverse all schema changes in correct order."""
    # Drop trigram indexes
    op.execute("DROP INDEX IF EXISTS ix_structures_name_en_trgm")
    op.execute("DROP INDEX IF EXISTS ix_structures_name_kk_trgm")
    op.execute("DROP INDEX IF EXISTS ix_structures_name_ru_trgm")

    # Drop tsvector GIN indexes
    op.execute("DROP INDEX IF EXISTS ix_structures_search_ts_en")
    op.execute("DROP INDEX IF EXISTS ix_structures_search_ts_kk")
    op.execute("DROP INDEX IF EXISTS ix_structures_search_ts_ru")

    # Drop tsvector generated columns
    op.execute("ALTER TABLE structures DROP COLUMN IF EXISTS search_ts_en")
    op.execute("ALTER TABLE structures DROP COLUMN IF EXISTS search_ts_kk")
    op.execute("ALTER TABLE structures DROP COLUMN IF EXISTS search_ts_ru")

    # Drop B-tree indexes
    op.drop_index("ix_structures_type", table_name="structures")
    op.drop_index("ix_structures_technical_condition", table_name="structures")
    op.drop_index("ix_structures_water_source", table_name="structures")
    op.drop_index("ix_structures_district", table_name="structures")

    # Drop filterable columns + status column
    op.drop_column("structures", "status")
    op.drop_column("structures", "structure_count")
    op.drop_column("structures", "cadastral_number")
    op.drop_column("structures", "commissioning_year")
    op.drop_column("structures", "wear_percentage")
    op.drop_column("structures", "technical_condition")
    op.drop_column("structures", "water_source")
    op.drop_column("structures", "district")

    # Restore NOT NULL on geometry
    op.execute("ALTER TABLE structures ALTER COLUMN geometry SET NOT NULL")
