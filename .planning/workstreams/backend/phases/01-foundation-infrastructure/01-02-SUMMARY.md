---
phase: 01-foundation-infrastructure
plan: 02
subsystem: database
tags: [alembic, postgis, sqlalchemy, provenance, minio, fastapi, pydantic]

# Dependency graph
requires:
  - "phase: 01-01, provides: Docker stack + FastAPI app + async engine + settings"
provides:
  - "ProvenanceModel ORM — source_type, confidence_level, recorded_at (DATA-07)"
  - "StructureModel with PostGIS Geometry(Point, srid=4326) — vector features only"
  - "StructureFactModel with JSONB attribute_value + provenance_id FK"
  - "MinIOService — ensure_bucket, presigned_upload_url (1hr), presigned_download_url (2hr)"
  - "Provenance CRUD API — POST /api/v1/provenance (201), GET by id, GET query"
  - "MinIO presigned URL endpoints — POST /api/v1/minio/presign, GET /api/v1/minio/presign/{object_name}"
  - "Alembic migration infrastructure with GeoAlchemy2 helpers"
  - "Initial migration 0001 creating provenance, structures, structure_facts tables"
affects: [phase-2, phase-3, phase-4, phase-5]

# Tech tracking
tech-stack:
  added: [alembic 1.18, geoalchemy2 alembic_helpers, psycopg3 sync driver]
  patterns: [SQLAlchemy 2.0 Mapped + mapped_column, Alembic manual migration with GeoAlchemy2 helpers, custom include_object for PostGIS extension table filtering, async DB service pattern (async_session + session.begin), Pydantic ConfigDict(from_attributes=True) for ORM, MinIOService wrapper class]

key-files:
  created:
    - apps/api/alembic.ini
    - apps/api/alembic/env.py
    - apps/api/alembic/versions/0001_initial.py
    - apps/api/src/api/models/__init__.py
    - apps/api/src/api/models/provenance.py
    - apps/api/src/api/models/structure.py
    - apps/api/src/api/services/__init__.py
    - apps/api/src/api/services/minio_client.py
    - apps/api/src/api/services/provenance_service.py
    - apps/api/src/api/routes/provenance.py
    - apps/api/src/api/routes/minio.py
    - apps/api/tests/test_provenance.py
    - apps/api/tests/test_minio.py
    - apps/api/tests/test_schema.py
  modified:
    - apps/api/src/api/main.py
    - apps/api/tests/conftest.py
    - apps/api/pyproject.toml

key-decisions:
  - "Used psycopg3 (postgresql+psycopg://) instead of psycopg2 for Alembic sync driver — project has psycopg[binary] not psycopg2"
  - "Custom include_object wraps alembic_helpers.include_object to also filter PostGIS Tiger geocoder extension tables (40+ tables from postgis Docker image)"
  - "Added ix_structures_geometry to spatial index exclusion set — raw-SQL GiST index not auto-detected by GeoAlchemy2 helper"
  - "Manual migration (not autogenerate) per RESEARCH.md Pitfall #5 — GeoAlchemy2 autogenerate breaks"
  - "Provenance tests mock service functions (not async_session) — tests route layer independently"
  - "Schema tests use real DB connection via psycopg3 sync engine — verify actual information_schema"
  - "test_fact_has_provenance uses real async DB session to prove NOT NULL FK enforcement (DATA-07)"

patterns-established:
  - "Pattern: SQLAlchemy 2.0 Mapped + mapped_column for all ORM models — no legacy Column()"
  - "Pattern: Alembic env.py with custom include_object wrapping GeoAlchemy2 helpers + PostGIS extension table filtering"
  - "Pattern: Async DB service via async_session() + session.begin() + flush + refresh (from thread_ownership.py analog)"
  - "Pattern: FastAPI route with Pydantic BaseModel + ConfigDict(from_attributes=True) for ORM serialization"
  - "Pattern: MinIOService wrapper class — ensure_bucket on startup, presigned URLs on demand"
  - "Pattern: TDD RED/GREEN — tests written first (9 fail), implementation second (16 pass)"
  - "Pattern: pytest.mark.integration for tests requiring running Docker stack"

requirements-completed: [DATA-07, INT-04]

# Metrics
duration: 7min
completed: 2026-06-25
---

# Plan 01-02: Provenance Schema + API + MinIO Presigned URLs Summary

**PostGIS schema with provenance tracking on all structure records, provenance CRUD REST API, MinIO presigned URL endpoints, and Alembic migration infrastructure — proving DATA-07 and INT-04 end-to-end**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-06-25T20:04:28Z
- **Completed:** 2026-06-25T20:11:18Z
- **Tasks:** 2 (1 auto + 1 TDD auto)
- **Files modified:** 17 (14 created + 3 modified)

## Accomplishments
- Alembic migration infrastructure with GeoAlchemy2 helpers — manual migration creates provenance, structures, structure_facts tables with GiST spatial index and check constraints
- Provenance CRUD API operational: POST /api/v1/provenance (201), GET by id (200/404), GET with source_type/confidence_level filters
- MinIO presigned URL endpoints operational: POST /api/v1/minio/presign (upload, 1hr expiry), GET /api/v1/minio/presign/{object_name} (download, 2hr expiry)
- Architecture separation proven: structures table has PostGIS Geometry column, no binary (bytea/oid) columns in structures or structure_facts (INT-04)
- Provenance FK enforcement proven: StructureFactModel without provenance_id raises IntegrityError (DATA-07)
- All 16 tests pass (5 health + 3 minio + 5 provenance CRUD + 1 FK enforcement + 2 schema separation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Alembic setup + ORM models + initial migration** - `58a6254` (feat)
2. **Task 2: Failing tests for provenance, MinIO, schema (TDD RED)** - `98c31c8` (test)
3. **Task 2: Provenance service + MinIO service + REST endpoints (TDD GREEN)** - `b000d48` (feat)

_Note: Task 2 is TDD — tests committed first (RED), then implementation (GREEN)_

## Files Created/Modified
- `apps/api/alembic.ini` - Alembic config with readable file_template, URL overridden in env.py
- `apps/api/alembic/env.py` - Migration env with GeoAlchemy2 helpers + custom include_object for PostGIS extension tables
- `apps/api/alembic/versions/0001_initial.py` - Manual migration creating provenance, structures, structure_facts tables
- `apps/api/src/api/models/provenance.py` - ProvenanceModel ORM with check constraint on confidence_level
- `apps/api/src/api/models/structure.py` - StructureModel (PostGIS Geometry) + StructureFactModel (JSONB)
- `apps/api/src/api/models/__init__.py` - Barrel export registering models on Base.metadata
- `apps/api/src/api/services/minio_client.py` - MinIOService class with ensure_bucket, presigned URLs
- `apps/api/src/api/services/provenance_service.py` - Async CRUD: create_provenance, get_provenance, query_provenance
- `apps/api/src/api/services/__init__.py` - Barrel export for MinIOService
- `apps/api/src/api/routes/provenance.py` - POST/GET/GET-list endpoints with Pydantic DTOs
- `apps/api/src/api/routes/minio.py` - POST presign upload, GET presign download endpoints
- `apps/api/src/api/main.py` - Modified: MinIOService in lifespan, provenance + minio routers registered
- `apps/api/tests/test_provenance.py` - 5 CRUD endpoint tests + 1 FK enforcement integration test
- `apps/api/tests/test_minio.py` - 3 presigned URL tests (upload, download, roundtrip)
- `apps/api/tests/test_schema.py` - 2 architecture separation tests (geometry in PostGIS, no binary)
- `apps/api/tests/conftest.py` - Updated MinIO mock path for MinIOService refactor
- `apps/api/pyproject.toml` - Added pytest integration marker

## Decisions Made
- Used psycopg3 (`postgresql+psycopg://`) instead of psycopg2 for Alembic sync driver — the project has `psycopg[binary,pool]` not `psycopg2`
- Created custom `include_object` wrapping `alembic_helpers.include_object` to filter 40+ PostGIS Tiger geocoder extension tables that ship with the postgis Docker image — without this, `alembic check` flags them as "removed tables"
- Added `ix_structures_geometry` to spatial index exclusion set — the raw-SQL GiST index created via `op.execute` isn't auto-detected by GeoAlchemy2's helper because it doesn't follow the `idx_*_gist` naming convention
- Wrote migration manually (not autogenerate) per RESEARCH.md Pitfall #5 — GeoAlchemy2 autogenerate produces broken migrations for spatial types
- Provenance endpoint tests mock service functions (not async_session) for clean route-layer isolation
- Schema and FK enforcement tests use real DB connections to verify actual database constraints

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] psycopg2 not installed — used psycopg3 instead**
- **Found during:** Task 1 (alembic upgrade head)
- **Issue:** Alembic sync URL `postgresql://` maps to psycopg2 driver, but project has `psycopg[binary]` (v3), not psycopg2
- **Fix:** Used `postgresql+psycopg://` driver prefix for sync database URL (overridden via `API_SYNC_DATABASE_URL` env var when running from host)
- **Files modified:** None (env var override only — settings.sync_database_url works as-is inside Docker where both drivers may be present)
- **Verification:** `alembic upgrade head` and `alembic check` both pass with psycopg3 driver
- **Committed in:** Part of Task 1 commit `58a6254`

**2. [Rule 3 - Blocking] PostGIS Tiger geocoder extension tables detected by alembic check**
- **Found during:** Task 1 (alembic check)
- **Issue:** The `postgis/postgis:17-3.5` Docker image pre-installs `postgis_tiger_geocoder` extension which creates 40+ tables (county, faces, addr, edges, etc.) — `alembic check` flagged them as "removed tables" because they're not in our models
- **Fix:** Created custom `include_object` function that wraps `alembic_helpers.include_object` and also excludes known PostGIS extension table names + raw-SQL spatial indexes
- **Files modified:** apps/api/alembic/env.py
- **Verification:** `alembic check` passes with "No new upgrade operations detected"
- **Committed in:** Part of Task 1 commit `58a6254`

**3. [Rule 1 - Bug] Uuid import error in migration file**
- **Found during:** Task 1 (alembic upgrade head)
- **Issue:** `from sqlalchemy.dialects.postgresql import JSONB, Uuid` — `Uuid` is in `sqlalchemy` top-level, not in `postgresql` dialect module (which has `UUID`)
- **Fix:** Changed to `from sqlalchemy import Uuid` and `from sqlalchemy.dialects.postgresql import JSONB`
- **Files modified:** apps/api/alembic/versions/0001_initial.py
- **Verification:** Migration applies cleanly
- **Committed in:** Part of Task 1 commit `58a6254`

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 bug)
**Impact on plan:** All auto-fixes necessary for alembic to work with the project's specific dependencies and Docker image. No scope creep.

## Issues Encountered
- PostGIS Tiger geocoder extension tables in the Docker image required custom alembic filtering — this is a known issue with the postgis Docker image and would affect any project using `alembic check` with GeoAlchemy2

## User Setup Required
None - no external service configuration required. The Docker stack from Plan 01-01 provides all infrastructure. Alembic migration is applied to the running PostgreSQL.

## Next Phase Readiness
- Provenance schema and CRUD API ready for Phase 2 ingestion pipeline (Kazvodhoz spreadsheet → provenance records → structure records)
- StructureModel with PostGIS Geometry ready for Phase 2 spatial data loading and TiPG vector tile serving
- StructureFactModel with JSONB ready for Phase 3 risk model attribute storage
- MinIOService ready for Phase 3 document attachment and Phase 4 STAC catalog
- Alembic infrastructure ready for all future schema migrations
- All 16 tests green — health, provenance, MinIO, schema separation

## TDD Gate Compliance

Task 2 followed the RED/GREEN cycle:
- **RED gate:** `test(01-02)` commit `98c31c8` — 9 tests written and verified failing (routes not implemented)
- **GREEN gate:** `feat(01-02)` commit `b000d48` — implementation written, all 16 tests pass
- Both gate commits present in git log in correct order

## Self-Check: PASSED

- All 14 created files verified present on disk
- All 3 task commits verified in git log (58a6254, 98c31c8, b000d48)
- All 16 tests passing (uv run pytest tests/ -x -v → 16 passed)
- alembic check passes (No new upgrade operations detected)

---
*Phase: 01-foundation-infrastructure*
*Completed: 2026-06-25*
