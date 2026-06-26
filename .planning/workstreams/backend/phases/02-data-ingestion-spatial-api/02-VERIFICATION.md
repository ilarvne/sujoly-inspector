---
phase: 02-data-ingestion-spatial-api
verified: 2026-06-25T22:26:25Z
status: gaps_found
score: 3/4 must-haves verified
overrides_applied: 0
gaps:
  - truth: "REST API endpoints operational for list, retrieve, search structures with multilingual FTS + pg_trgm fuzzy matching"
    status: failed
    reason: "Search endpoint GET /api/v1/structures/search returns HTTP 500 Internal Server Error for any query that returns results. The FTS + pg_trgm SQL query works correctly (verified via direct DB query returning ranked results), but the HTTP response serialization crashes: SearchResultResponse.model_validate(model) fails because `match_score` is declared as a required field (no default) in the Pydantic schema, while StructureModel has no `match_score` attribute. Pydantic raises ValidationError 'Field required [type=missing]'. The unit tests pass because they mock search_structures with MagicMock objects, and MagicMock.__float__() returns 0.0 for any attribute access — masking the bug. In production with real StructureModel instances, the attribute is missing and validation fails."
    artifacts:
      - path: "apps/api/src/api/schemas/structures.py"
        issue: "SearchResultResponse declares `match_score: float` as required (no default). StructureModel passed to model_validate() does not have this attribute, causing ValidationError."
      - path: "apps/api/src/api/routes/structures.py"
        issue: "Line 140: `resp = SearchResultResponse.model_validate(model)` crashes when model is a real StructureModel. The `resp.match_score = score` assignment on line 141 never executes because validation fails first."
    missing:
      - "Give match_score a default value in SearchResultResponse: `match_score: float = 0.0` (route overwrites it afterward), OR construct response from StructureResponse first then add match_score: `resp = StructureResponse.model_validate(model); results.append(SearchResultResponse(**resp.model_dump(), match_score=score))`"
      - "Add an integration test that calls the real search endpoint (not mocked) against a running DB to catch serialization bugs that unit tests with MagicMock miss"
---

# Phase 2: Data Ingestion & Spatial API — Verification Report

**Phase Goal:** Kazvodhoz registry ingested into PostGIS with correct coordinates, searchable, accessible via OGC API and REST
**Verified:** 2026-06-25T22:26:25Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | All 444 Kazvodhoz canal records loaded into PostGIS with correctly transformed coordinates — no 50-200m offset | ✓ VERIFIED | 230 structures loaded into PostGIS (count > 0 per D-01/D-02 adjusted criteria). All 230 have NULL geometry (D-02: geometry nullable — spreadsheet has NO coordinates per CONTEXT.md D-01). 231 provenance records with source_type='kazvodhoz_spreadsheet'. 1768 structure_facts (D-07 provenance-per-fact). The 444→230 difference: spreadsheet has 444 total rows but only 230 are actual data rows; headers/group/summary rows correctly skipped by parse_kazvodhoz_sheet. Coordinates deferred to Phase 4 per D-02. |
| 2   | External GIS client (QGIS) can connect to OGC API Features/Tiles via TiPG and load structures with filtering | ✓ VERIFIED (API) + human needed (QGIS) | TiPG container healthy on port 8080. GET /collections includes `public.structures` (auto-discovered). CQL2 filtering works live: `filter=type='canal'&filter-lang=cql2-text` returns FeatureCollection with type='canal' features. TileJSON endpoint returns tile URL template. NULL geometry returns `geometry: null` in GeoJSON. All 7 TiPG integration tests pass. QGIS GUI connection requires human verification. |
| 3   | REST API endpoints operational for list, retrieve, search structures with multilingual FTS + pg_trgm fuzzy matching | ✗ FAILED | List (GET /structures) and retrieve (GET /structures/{id}) work. But **search endpoint (GET /structures/search) returns HTTP 500** for any query matching results. Root cause: `SearchResultResponse.model_validate(model)` fails — `match_score` is required in schema but StructureModel lacks it. The FTS + pg_trgm SQL query itself works (verified via direct DB query: `ts_rank_cd` returns 0.4 for "Иртыш" water_source matches). Bug is in response serialization only. Unit tests pass because MagicMock masks the missing attribute. |
| 4   | CRUD endpoints operational for the application frontend | ✓ VERIFIED | All 6 CRUD endpoints verified live: GET /structures (200, total=230, pagination), GET /structures/{id} (200/404), POST /structures (201), PUT /structures/{id} (200, provenance-per-fact update with new provenance_id), DELETE /structures/{id} (200, soft delete status='deleted'), GET deleted returns 404. |

**Score:** 3/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `apps/api/alembic/versions/0002_add_filterable_columns_and_search.py` | Migration: nullable geometry, 7 filterable columns, 3 tsvector, trigram indexes | ✓ VERIFIED | 136 lines. revision="0002", down_revision="0001". DROP NOT NULL via raw SQL (Pitfall #7). 7 filterable columns + status. 3 generated tsvector columns (russian/simple/english). 3 GIN tsvector indexes + 3 GIN trigram indexes. Full downgrade. Applied to live DB (verified: columns + indexes + pg_trgm extension exist). |
| `apps/api/src/api/services/ingestion_service.py` | Spreadsheet parsing, cross-sheet enrichment, bulk insert with provenance | ✓ VERIFIED | 302 lines. parse_kazvodhoz_sheet (skips headers/summaries, float→int conversion), enrich_with_cross_sheet_data (3-sheet join by row_num), bulk_insert_structures (sync psycopg, idempotent via source_reference, creates ProvenanceModel+StructureModel+StructureFactModel). 230 records + 1768 facts ingested. |
| `apps/api/src/api/routes/ingestion.py` | POST /ingestion/kazvodhoz (202+job_id), GET status | ✓ VERIFIED | 93 lines. POST returns 202 with job_id via Celery .delay(). .xls validation + 10MB limit (T-02-04). GET polls AsyncResult status. Wired to celery task. |
| `apps/api/src/api/schemas/structures.py` | Pydantic models for CRUD + search | ⚠️ HAS BUG | 125 lines. StructureCreate, StructureUpdate, StructureResponse (ConfigDict), StructureListResponse, SearchListResponse all correct. **SearchResultResponse has `match_score: float` with no default — causes production 500 error.** |
| `apps/api/src/api/services/structure_service.py` | Async CRUD + FTS/trigram search + bbox + pagination | ✓ VERIFIED | 372 lines. create/get/list/search/update/delete all implemented. search_structures uses ts_rank_cd + similarity() with blended_score (0.7 FTS + 0.3 trigram), lang→tsvector column mapping, @@ plainto_tsquery OR % trigram. bbox via ST_MakeEnvelope + ST_Intersects with NULL guard. Provenance-per-fact update. Soft delete. |
| `apps/api/src/api/routes/structures.py` | REST endpoints: list, search, get, post, put, delete | ⚠️ HAS BUG | 222 lines. All 6 endpoints defined with correct params. List supports filters+bbox+pagination+geojson. **Line 140: SearchResultResponse.model_validate(model) crashes for real StructureModel.** |
| `apps/api/src/api/models/structure.py` | StructureModel with nullable geometry + filterable columns | ✓ VERIFIED | geometry nullable=True (D-02). 7 filterable Mapped columns + status. tsvector columns correctly NOT declared as ORM types. |
| `apps/api/src/api/tasks/celery_tasks.py` | ingest_kazvodhoz_task Celery task | ✓ VERIFIED | @celery_app.task(bind=True, name="ingest_kazvodhoz"). Calls bulk_insert_structures. Wired from route via .delay(). |
| `docker-compose.yml` (tipg service) | TiPG as 6th Docker Compose service | ✓ VERIFIED | image ghcr.io/developmentseed/tipg:latest, DATABASE_URL (not TIPG_DATABASE_URL), TIPG_* env vars, port 8080, healthcheck /healthz, depends_on postgres service_healthy, TIPG_DB_SPATIAL_EXTENT=false. Container running healthy. |
| `apps/api/tests/test_ingestion.py` | Unit tests for ingestion | ✓ VERIFIED | 7 tests, all pass. TestIngestionParsing, TestIngestionIdempotency, TestIngestionProvenance. |
| `apps/api/tests/test_structures.py` | Unit tests for CRUD + search | ⚠️ INSUFFICIENT | 11 tests pass but search tests mock service with MagicMock, masking the production serialization bug. Tests verify mock behavior, not real endpoint behavior. |
| `apps/api/tests/test_tipg.py` | Integration tests for OGC API | ✓ VERIFIED | 7 @pytest.mark.integration tests, all pass against live TiPG. Collection discovery, GeoJSON, CQL2, TileJSON, NULL geometry, pagination, healthz. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| routes/ingestion.py | tasks/celery_tasks.py | ingest_kazvodhoz_task.delay() | ✓ WIRED | Line 74: `task = ingest_kazvodhoz_task.delay(filepath=filepath, force=force)`. Returns job_id. |
| tasks/celery_tasks.py | services/ingestion_service.py | bulk_insert_structures() | ✓ WIRED | Line 36: `return bulk_insert_structures(filepath=filepath, force=force)` |
| ingestion_service.py | models/structure.py | StructureModel + ProvenanceModel + StructureFactModel | ✓ WIRED | Creates all 3 models per record. 230 structures + 231 provenance + 1768 facts in DB. |
| routes/structures.py | services/structure_service.py | service function calls | ✓ WIRED | All 6 service functions imported and called. |
| structure_service.py | StructureModel + tsvector columns | ts_rank_cd + similarity | ✓ WIRED | search_structures uses literal_column for tsvector, func.ts_rank_cd, func.similarity. SQL verified working via direct DB query. |
| main.py | structures + ingestion routers | app.include_router | ✓ WIRED | Line 17: imports both. Lines 127-128: include_router for both. CORS allows PUT (line 119). |
| docker-compose tipg | postgres | DATABASE_URL + depends_on | ✓ WIRED | DATABASE_URL points to postgres:5432. depends_on postgres condition: service_healthy. Container healthy. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| ingestion_service.py | records list | xlrd.open_workbook(датасет.xls) | Yes — 230 records parsed from real spreadsheet | ✓ FLOWING |
| routes/ingestion.py | job_id | Celery AsyncResult.task.id | Yes — real Celery task dispatched | ✓ FLOWING |
| structure_service.py (list) | items, total | SQLAlchemy select(StructureModel) | Yes — 230 structures in DB | ✓ FLOWING |
| structure_service.py (search) | items_with_score | SQLAlchemy select + ts_rank_cd + similarity | Yes — SQL returns ranked results (fts_rank=0.4 for "Иртыш") | ✓ FLOWING (SQL) / ✗ BROKEN (HTTP serialization) |
| routes/structures.py (search) | SearchListResponse | SearchResultResponse.model_validate(model) | No — crashes with ValidationError before returning | ✗ DISCONNECTED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| TiPG healthz | curl http://localhost:8080/healthz | HTTP 200 | ✓ PASS |
| TiPG collections | curl http://localhost:8080/collections | includes public.structures | ✓ PASS |
| TiPG CQL2 filter | curl ".../items?filter=type='canal'&filter-lang=cql2-text" | FeatureCollection, all type='canal' | ✓ PASS |
| TiPG TileJSON | curl ".../tilejson.json" | tiles URL template returned | ✓ PASS |
| TiPG NULL geometry | curl ".../items?limit=1" | geometry: null | ✓ PASS |
| REST list | curl http://localhost:8000/api/v1/structures?limit=2 | total=230, 2 items | ✓ PASS |
| REST GeoJSON | curl .../structures?format=geojson&limit=1 | FeatureCollection, 1 feature | ✓ PASS |
| REST POST | curl -X POST .../structures | HTTP 201, structure created | ✓ PASS |
| REST PUT | curl -X PUT .../structures/{id} | HTTP 200, updated fields + new provenance_id | ✓ PASS |
| REST DELETE | curl -X DELETE .../structures/{id} | HTTP 200, {"status":"deleted"} | ✓ PASS |
| REST GET deleted | curl .../structures/{deleted_id} | HTTP 404 | ✓ PASS |
| REST search (no match) | curl .../search?q=zzzznomatch | HTTP 200, items=[], total=0 | ✓ PASS |
| REST search (match) | curl .../search?q=Иртыш&lang=ru | HTTP 500 Internal Server Error | ✗ FAIL |
| DB count structures | psql SELECT count(*) FROM structures | 230 | ✓ PASS |
| DB NULL geometry | psql SELECT count(*) WHERE geometry IS NULL | 230 (all) | ✓ PASS |
| DB provenance | psql SELECT count(*) WHERE source_type='kazvodhoz_spreadsheet' | 231 | ✓ PASS |
| DB FTS search | psql ... plainto_tsquery('russian','Иртыш') | 3 rows, fts_rank=0.4 | ✓ PASS |
| Test suite | pytest tests/ -q | 39 passed, 1 failed (pre-existing), 2 skipped | ✓ PASS (Phase 2 tests) |

### Probe Execution

No phase-declared probe scripts found (no `scripts/*/tests/probe-*.sh`). Integration tests in `tests/test_tipg.py` serve as the probe equivalent — all 7 pass against live Docker stack.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| DATA-01 | 02-01 | Spreadsheet ingestion into PostGIS with coordinate transformation (QazTRF-23 moot per D-01) | ✓ DELIVERED | Ingestion pipeline reads датасет.xls with xlrd, cross-references 3 sheets, bulk-inserts 230 structures with provenance + facts. Geometry NULL per D-01/D-02 (no coordinates in spreadsheet). QazTRF-23 transformation moot per D-01. |
| DATA-08 | 02-02 | Search/filter endpoints with multilingual FTS + pg_trgm fuzzy matching | ✗ PARTIAL | Search logic correctly implemented (FTS ts_rank_cd + pg_trgm similarity with blended score, verified via direct SQL). BUT search HTTP endpoint returns 500 for matching queries due to SearchResultResponse serialization bug. Filter endpoints (type, district, etc.) work via list endpoint. |
| INT-01 | 02-03 | OGC API Features/Tiles via TiPG for external GIS clients | ✓ DELIVERED | TiPG container running, auto-discovers public.structures, CQL2 filtering works, TileJSON endpoint works, NULL geometry handled. 7 integration tests pass. |
| INT-03 | 02-01, 02-02 | REST API for frontend (CRUD, search, ingestion, sync endpoints) | ✗ PARTIAL | CRUD endpoints (GET/POST/PUT/DELETE) all operational. Ingestion endpoints (POST/GET) operational. Search endpoint broken (500 error). Sync endpoints not in Phase 2 scope (deferred). |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| tests/test_structures.py | 208-244 | Search tests mock service with MagicMock, masking production serialization bug | ⚠️ Warning | Tests pass but production fails — MagicMock.__float__() returns 0.0 for any attribute, so model_validate succeeds in tests but crashes with real StructureModel. No integration test exercises the real search→serialize path. |
| apps/api/src/api/schemas/structures.py | 116 | `match_score: float` required field with no default on subclass of StructureResponse | 🛑 Blocker | SearchResultResponse.model_validate(StructureModel) fails because StructureModel has no match_score attribute. Causes HTTP 500 on every search query that returns results. |

### Human Verification Required

### 1. QGIS Connection to TiPG OGC API

**Test:** Open QGIS → Add Vector Layer → OGC API Features → URL: http://localhost:8080/collections/public.structures/items → load structures with CQL2 filtering
**Expected:** Structures load as a vector layer in QGIS, CQL2 filter (e.g., type='canal') applies correctly, attribute table shows structure data
**Why human:** QGIS GUI interaction cannot be verified programmatically. API endpoints verified via curl (CQL2, GeoJSON, TileJSON all return correct responses), but the actual QGIS client connection workflow requires manual testing.

---

### Gaps Summary

**1 BLOCKER gap found:**

**Search endpoint serialization bug (SC3, DATA-08, INT-03):** The `GET /api/v1/structures/search` endpoint returns HTTP 500 Internal Server Error for any query that matches results. The root cause is a Pydantic validation failure: `SearchResultResponse` declares `match_score: float` as a required field (no default), but the route calls `SearchResultResponse.model_validate(model)` where `model` is a `StructureModel` that doesn't have a `match_score` attribute. The search SQL query itself works perfectly (verified via direct database query — FTS ranking returns 0.4 for "Иртыш" matches), so the bug is isolated to the HTTP response serialization layer.

The unit tests (test_fts_search, test_fuzzy_search, test_combined_search) all pass because they mock `search_structures` with MagicMock objects. MagicMock returns 0.0 for any attribute access via `__float__()`, so `model_validate` succeeds in tests. In production with real `StructureModel` instances, the attribute is missing and validation crashes. This is a classic "tests pass but production fails" anti-pattern caused by over-mocking.

**Fix:** Add a default value to `match_score` in `SearchResultResponse` (`match_score: float = 0.0`), or construct the response from `StructureResponse` first then add match_score explicitly. Add an integration test that calls the real (non-mocked) search endpoint against a running database.

---

_Verified: 2026-06-25T22:26:25Z_
_Verifier: the agent (gsd-verifier)_
