---
phase: 02-data-ingestion-spatial-api
plan: 01
subsystem: database
tags: [xlrd, celery, alembic, postgis, tsvector, pg_trgm, fastapi, ingestion]

# Dependency graph
requires:
  - phase: 01-foundation-infrastructure
    provides: "ProvenanceModel, StructureModel, StructureFactModel, Celery app, async/sync database infrastructure, route/service patterns"
provides:
  - "Spreadsheet ingestion pipeline (xlrd → PostGIS with cross-sheet enrichment)"
  - "Migration 0002: nullable geometry, 7 filterable columns, 3 tsvector generated columns, trigram indexes, status column"
  - "POST /api/v1/ingestion/kazvodhoz endpoint with Celery task dispatch"
  - "GET /api/v1/ingestion/kazvodhoz/{job_id} status polling endpoint"
  - "Idempotent ingestion via source_reference provenance check"
  - "StructureModel with filterable denormalized columns for D-08 search/filter"
affects: [02-02, 02-03, 03-risk-assessment, 04-discovery-matching]

# Tech tracking
tech-stack:
  added: [xlrd>=2.0.2]
  patterns:
    - "Sync psycopg bulk insert via create_engine + Session (D-17) for Celery tasks"
    - "Cross-sheet spreadsheet enrichment using row number as join key (D-18)"
    - "Generated tsvector columns with setweight() for multilingual FTS (D-10)"
    - "Raw SQL op.execute for nullable geometry to preserve GiST index (Pitfall #7)"
    - "Idempotent ingestion via source_reference provenance check (D-19)"
    - "File upload validation: .xls extension + 10MB size limit (T-02-04)"

key-files:
  created:
    - apps/api/alembic/versions/0002_add_filterable_columns_and_search.py
    - apps/api/src/api/services/ingestion_service.py
    - apps/api/src/api/routes/ingestion.py
    - apps/api/tests/test_ingestion.py
  modified:
    - apps/api/src/api/models/structure.py
    - apps/api/src/api/tasks/celery_tasks.py
    - apps/api/src/api/main.py
    - apps/api/pyproject.toml
    - apps/api/tests/conftest.py

key-decisions:
  - "Used raw SQL op.execute for nullable geometry (Pitfall #7) instead of op.alter_column to preserve GiST spatial index"
  - "Used 'simple' FTS config for Kazakh (no dedicated Kazakh config exists in PostgreSQL)"
  - "Added status column with server_default='active' for soft-delete support (D-13)"
  - "Did not declare tsvector columns as ORM Mapped types — they are GENERATED columns managed by PostgreSQL"
  - "xlrd 2.0.2 selected as only library that reads legacy .xls format (openpyxl does not support .xls)"

patterns-established:
  - "Pattern: Sync bulk insert for Celery tasks — create_engine(settings.sync_database_url) + Session(engine) for batch operations"
  - "Pattern: Cross-sheet enrichment — build lookup dicts keyed by row_num, merge preferring primary sheet data"
  - "Pattern: Idempotent ingestion — check source_reference in provenance table before insert, skip if exists and force=False"
  - "Pattern: File upload security — validate extension (.xls only) and size (<10MB) before processing"

requirements-completed: [DATA-01, INT-03]

# Metrics
duration: 6min
completed: 2026-06-25
---

# Phase 2 Plan 01: Data Ingestion Summary

**Kazvodhoz spreadsheet ingestion pipeline with xlrd parsing, cross-sheet enrichment, Celery task dispatch, and Alembic migration for nullable geometry + filterable columns + multilingual FTS + trigram indexes**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-25T21:52:55Z
- **Completed:** 2026-06-25T21:59:11Z
- **Tasks:** 2
- **Files modified:** 9 (4 created, 5 modified)

## Accomplishments
- Migration 0002 makes geometry nullable (D-02), adds 7 filterable columns (D-08), 3 generated tsvector columns for multilingual FTS (D-10), GIN trigram indexes for fuzzy matching (D-11), and status column for soft-delete (D-13)
- Ingestion service parses Kazvodhoz .xls spreadsheet with xlrd, handles float-to-int cell type conversion (Pitfall #1), skips header/summary rows (Pitfall #2), and cross-references all 3 sheets using row number as join key (D-18, Pitfall #3)
- Celery task `ingest_kazvodhoz` dispatches bulk insert with sync psycopg connection, creates ProvenanceModel + StructureModel + StructureFactModel per record, and is idempotent via source_reference check (D-19, D-20)
- API endpoints: POST /api/v1/ingestion/kazvodhoz returns 202 with job_id, GET /api/v1/ingestion/kazvodhoz/{job_id} polls Celery AsyncResult status
- File upload validation: .xls extension only + 10MB size limit (T-02-04 threat mitigation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Alembic migration 0002 + model update + xlrd dependency** - `41cac37` (test — RED phase)
2. **Task 2: Ingestion service + Celery task + API route** - `cc4ce2f` (feat — GREEN phase)

_Note: TDD tasks have multiple commits (test → feat)_

## Files Created/Modified
- `apps/api/alembic/versions/0002_add_filterable_columns_and_search.py` - Migration: nullable geometry, 7 filterable columns, 3 tsvector generated columns, GIN indexes, trigram indexes, status column
- `apps/api/src/api/services/ingestion_service.py` - parse_kazvodhoz_sheet, enrich_with_cross_sheet_data, bulk_insert_structures
- `apps/api/src/api/routes/ingestion.py` - POST /ingestion/kazvodhoz (202+job_id), GET /ingestion/kazvodhoz/{job_id} (status), .xls validation
- `apps/api/tests/test_ingestion.py` - TestIngestionParsing, TestIngestionIdempotency, TestIngestionProvenance (7 tests)
- `apps/api/src/api/models/structure.py` - Added nullable geometry, 7 filterable Mapped columns, status column
- `apps/api/src/api/tasks/celery_tasks.py` - Added ingest_kazvodhoz_task with bind=True
- `apps/api/src/api/main.py` - Registered ingestion router, added PUT to CORS
- `apps/api/pyproject.toml` - Added xlrd>=2.0.2 dependency
- `apps/api/tests/conftest.py` - Added mock_xlrd_sheet fixture

## Decisions Made
- Used raw SQL `op.execute("ALTER TABLE structures ALTER COLUMN geometry DROP NOT NULL")` instead of `op.alter_column(nullable=True)` to preserve the existing GiST spatial index (Pitfall #7 from RESEARCH.md)
- Used `'simple'` PostgreSQL FTS config for Kazakh tsvector since no dedicated Kazakh config exists
- Added `status` column with `server_default="active"` for soft-delete support per D-13
- Did not declare tsvector columns as ORM Mapped types — they are PostgreSQL GENERATED columns managed by the database, not written by the application (PATTERNS.md line 146)
- Selected xlrd 2.0.2 as the only library that reads legacy .xls format (openpyxl does not support .xls)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tests pass on first implementation. The TDD RED/GREEN cycle completed cleanly: 7 tests failed in RED (ModuleNotFoundError for ingestion_service), then all 7 passed in GREEN after implementation.

## User Setup Required

None - no external service configuration required. xlrd is a pure Python library with no external dependencies. The ingestion pipeline uses the existing Docker stack (PostgreSQL, Redis, Celery) from Phase 1.

## Next Phase Readiness
- Migration 0002 ready to apply (requires Docker postgres running): `alembic upgrade head`
- Ingestion pipeline ready to run: POST /api/v1/ingestion/kazvodhoz triggers Celery task
- StructureModel updated with filterable columns — ready for Plan 02 (structures CRUD + search endpoints)
- FTS + trigram indexes created by migration — ready for Plan 02 search endpoint implementation
- TiPG container configuration deferred to Plan 03 (OGC API Features/Tiles)

## Self-Check: PASSED

- All 4 created files verified on disk: migration 0002, ingestion_service.py, routes/ingestion.py, test_ingestion.py
- Both task commits verified in git log: 41cac37 (RED), cc4ce2f (GREEN)
- All 7 ingestion tests pass (GREEN)
- Full test suite: 21 passed, 2 skipped, 1 deselected — no regressions

---
*Phase: 02-data-ingestion-spatial-api*
*Completed: 2026-06-25*
