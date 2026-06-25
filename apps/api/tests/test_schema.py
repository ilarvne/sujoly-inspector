"""Tests for architecture separation (INT-04).

Verifies that:
- structures table has a geometry column (PostGIS vector features)
- No binary columns (bytea, oid) in structures or structure_facts tables
  (binary assets belong in MinIO, not PostgreSQL)
"""

import os

import pytest
from sqlalchemy import create_engine, text

from api.config.settings import settings


def _get_db_url() -> str:
    """Get a sync DB URL for host access (replace postgres hostname with localhost)."""
    url = os.environ.get(
        "API_SYNC_DATABASE_URL",
        settings.sync_database_url,
    )
    # Replace Docker hostname with localhost for host-side tests
    return url.replace("postgres:5432", "localhost:5432").replace(
        "postgresql://", "postgresql+psycopg://"
    )


def _db_available() -> bool:
    """Check if the database is reachable."""
    try:
        engine = create_engine(_get_db_url())
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


# Skip all tests in this module if DB is not available
pytestmark = pytest.mark.skipif(
    not _db_available(), reason="PostgreSQL not available — integration tests require running Docker stack"
)


class TestSchemaArchitectureSeparation:
    """Tests for INT-04: architecture separation between PostGIS and MinIO."""

    def test_geometry_in_postgis(self):
        """structures table has a geometry column of type Geometry.

        This proves vector features are stored in PostGIS (INT-04).
        """
        engine = create_engine(_get_db_url())
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT column_name, data_type, udt_name "
                    "FROM information_schema.columns "
                    "WHERE table_name = 'structures' AND column_name = 'geometry'"
                )
            )
            row = result.fetchone()
        engine.dispose()

        assert row is not None, "geometry column not found in structures table"
        col_name, data_type, udt_name = row
        assert col_name == "geometry"
        # PostGIS geometry columns show as USER-DEFINED type with udt_name = 'geometry'
        assert data_type == "USER-DEFINED", f"Expected USER-DEFINED, got {data_type}"
        assert udt_name == "geometry", f"Expected udt_name=geometry, got {udt_name}"

    def test_no_binary_in_postgis(self):
        """No bytea, oid, or blob columns in structures or structure_facts tables.

        This proves binary assets are NOT stored in PostgreSQL (INT-04).
        Binary assets belong in MinIO buckets.
        """
        engine = create_engine(_get_db_url())
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name, column_name, data_type "
                    "FROM information_schema.columns "
                    "WHERE table_name IN ('structures', 'structure_facts') "
                    "AND data_type IN ('bytea', 'oid', 'blob', 'binary', 'varbinary')"
                )
            )
            rows = result.fetchall()
        engine.dispose()

        assert len(rows) == 0, (
            f"Found binary columns in structures/structure_facts (violates INT-04): {rows}"
        )
