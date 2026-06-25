---
phase: 02-data-ingestion-spatial-api
plan: 02
subsystem: api
tags: [fastapi, pydantic, sqlalchemy, postgis, tsvector, pg_trgm, fts, rest, crud, search]

# Dependency graph
requires:
  - phase: 02-data-ingestion-spatial-api/plan-01
    provides: "Migration 0002 with nullable geometry, filterable columns, tsvector generated columns, trigram indexes, status column; StructureModel with filterable Mapped columns"
provides:
  - "REST CRUD endpoints at /api/v1/structures (GET list, GET by id, POST create, PUT update, DELETE soft-delete)"
  - "GET /api/v1/structures/search with combined FTS + pg_trgm fuzzy matching and blended score"
  - "Pydantic schemas: StructureCreate, StructureUpdate, StructureResponse, StructureListResponse, SearchResultResponse, SearchListResponse"
  - "Structure service layer with async CRUD, multilingual search, bbox spatial filter, provenance-per-fact update"
  - "GeoJSON FeatureCollection response format for map clients"
  - "Pagination envelope with total count for frontend pagination UI"
affects: [03-risk-assessment, 04-discovery-matching, frontend-workstream]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Combined FTS + trigram search with blended score (fts_rank * 0.7 + trigram * 0.3) per D-12"
    - "Provenance-per-fact update: expire old facts (valid_to=now) + create new provenance + new facts per D-13"
    - "bbox spatial filter via ST_MakeEnvelope + ST_Intersects with NULL geometry guard (T-02-03)"
    - "GeoJSON FeatureCollection response format option for map clients (D-16)"
    - "Pagination envelope {items, total, offset, limit} for list/search endpoints (D-16)"
    - "Soft delete via status='deleted' field (D-13)"
    - "literal_column for tsvector GENERATED columns not declared as ORM Mapped types"

key-files:
  created:
    - apps/api/src/api/schemas/structures.py
    - apps/api/src/api/services/structure_service.py
    - apps/api/src/api/routes/structures.py
    - apps/api/tests/test_structures.py
    - apps/api/src/api/schemas/__init__.py
  modified:
    - apps/api/src/api/main.py
    - apps/api/tests/conftest.py

key-decisions:
  - "Used literal_column() for tsvector GENERATED columns since they are not declared as ORM Mapped types"
  - "Used ValueError for bbox validation in service layer, caught by route layer as HTTPException 400"
  - "Used response_model=None for list endpoint to support both JSON and GeoJSON response formats"
  - "Search endpoint uses 'condition' param name mapped to 'technical_condition' filter per D-14"
  - "Soft-deleted structures (status='deleted') excluded from list and search queries"

patterns-established:
  - "Pattern: Combined FTS + trigram search — select tsvector column by lang, compute blended_score = fts_rank * 0.7 + greatest(similarity) * 0.3, WHERE clause uses @@ plainto_tsquery OR % trigram operator"
  - "Pattern: Provenance-per-fact update — create new ProvenanceModel, expire old StructureFactModel rows (valid_to=now), create new facts for changed fields, update StructureModel directly"
  - "Pattern: Dual-format endpoint — response_model=None with conditional return (Pydantic model for JSON, dict for GeoJSON)"
  - "Pattern: Service raises ValueError for invalid input, route catches and returns HTTPException 400"

requirements-completed: [DATA-08, INT-03]

# Metrics
duration: 6min
completed: 2026-06-25
---

# Phase 2 Plan 02: REST API + Multilingual Search Summary

**FastAPI REST CRUD endpoints with combined PostgreSQL FTS (ts_rank_cd) + pg_trgm fuzzy matching (blended score), bbox spatial filter, GeoJSON format, and provenance-per-fact update**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-25T22:04:46Z
- **Completed:** 2026-06-25T22:10:55Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 7 (5 created, 2 modified)

## Accomplishments
- REST CRUD endpoints operational at /api/v1/structures (GET list, GET by id, POST create 201, PUT update, DELETE soft-delete) per D-13
- Search endpoint at /api/v1/structures/search combines FTS (ts_rank_cd) with pg_trgm fuzzy matching (similarity) using blended score (fts_rank * 0.7 + trigram * 0.3) per D-12
- List endpoint supports attribute filters (type, district, technical_condition, water_source), bbox spatial filter, offset/limit pagination with total count, and GeoJSON format option per D-16
- PUT endpoint implements full D-13 provenance-per-fact update: creates new ProvenanceModel, expires old StructureFactModel rows, creates new facts for changed fields
- All queries use SQLAlchemy 2.0 parameterized ORM constructs (T-02-01 mitigation); bbox parsed to floats with validation (T-02-03 mitigation); limit constrained to prevent DoS (T-02-05 mitigation)

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED: Failing tests for structure CRUD and search endpoints** - `b0b90dc` (test)
2. **Task 1 GREEN: Structure REST API with multilingual FTS + trigram search** - `674ff5f` (feat)

_Note: TDD tasks have multiple commits (test → feat)_

## Files Created/Modified
- `apps/api/src/api/schemas/structures.py` - Pydantic models: StructureCreate, StructureUpdate, StructureResponse (ConfigDict from_attributes=True), StructureListResponse, SearchResultResponse, SearchListResponse
- `apps/api/src/api/services/structure_service.py` - Async CRUD + combined FTS/trigram search + bbox spatial filter + provenance-per-fact update + soft delete
- `apps/api/src/api/routes/structures.py` - REST endpoints: GET /structures (list+filter+search+bbox+pagination+geojson), GET /structures/search, GET/POST/PUT/DELETE /structures/{id}
- `apps/api/tests/test_structures.py` - TestStructureEndpoints class with 11 test functions
- `apps/api/src/api/schemas/__init__.py` - New schemas package init
- `apps/api/src/api/main.py` - Added structures router import + app.include_router(structures.router)
- `apps/api/tests/conftest.py` - Added mock_structure, mock_structure_list, mock_search_results fixtures

## Decisions Made
- Used `literal_column()` for tsvector GENERATED columns (search_ts_ru/kk/en) since they are PostgreSQL-generated, not ORM Mapped types — the ORM model does not declare them
- Used `ValueError` for bbox validation in the service layer, caught by the route layer as `HTTPException(400)` — keeps service testable without FastAPI dependency while satisfying T-02-03 mitigation
- Used `response_model=None` for the list endpoint to support both JSON (StructureListResponse) and GeoJSON (FeatureCollection dict) response formats in a single route
- Search endpoint uses `condition` param name (per D-14 spec) mapped to `technical_condition` filter internally
- Soft-deleted structures (status='deleted') excluded from list and search queries via `StructureModel.status != "deleted"` WHERE clause

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all 11 structure tests pass on first GREEN implementation. The TDD RED/GREEN cycle completed cleanly: 11 tests failed in RED (AttributeError: module 'api.routes' has no attribute 'structures'), then all 11 passed in GREEN after implementation.

## User Setup Required

None - no external service configuration required. All endpoints use the existing Docker stack (PostgreSQL, Redis) from Phase 1. The search functionality depends on the tsvector and trigram indexes created by Migration 0002 (Plan 01).

## Next Phase Readiness
- Structure REST API complete — ready for frontend workstream consumption
- Search endpoint ready for integration with map-first UI
- GeoJSON format option ready for MapLibre vector source consumption
- Pagination envelope ready for frontend pagination components
- PUT provenance-per-fact update pattern established for Phase 3+ data modifications
- TiPG OGC API (Plan 03) provides complementary standards-based access for external GIS clients

## Self-Check: PASSED

- All 5 created files verified on disk: schemas/structures.py, structure_service.py, routes/structures.py, test_structures.py, schemas/__init__.py
- Both task commits verified in git log: b0b90dc (RED), 674ff5f (GREEN)
- All 11 structure endpoint tests pass (GREEN)
- Full test suite: 38 passed, 2 failed (pre-existing integration tests requiring Docker), 2 skipped — no regressions
- All 19 acceptance criteria verified via grep and Python import checks

---
*Phase: 02-data-ingestion-spatial-api*
*Completed: 2026-06-25*
