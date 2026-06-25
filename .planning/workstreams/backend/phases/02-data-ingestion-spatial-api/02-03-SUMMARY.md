---
phase: 02-data-ingestion-spatial-api
plan: 03
subsystem: api
tags: [tipg, ogc-api, docker, cql2, geojson, vector-tiles, integration-tests]

# Dependency graph
requires:
  - phase: 02-data-ingestion-spatial-api/plan-01
    provides: "Migration 0002 (nullable geometry, filterable columns), ingestion pipeline with 230 structures ingested"
provides:
  - "TiPG container as 6th Docker Compose service on port 8080 (OGC API Features + Tiles)"
  - "OGC API Features collection auto-discovery for public.structures"
  - "CQL2 filtering on items endpoint (type='canal')"
  - "TileJSON endpoint for MapLibre vector tile consumption"
  - "NULL geometry handling — geometry: null in GeoJSON (D-02)"
  - "7 integration tests verifying all OGC API endpoints"
  - ".env.example TiPG configuration section"
affects: [04-discovery-matching, frontend-workstream]

# Tech tracking
tech-stack:
  added: [ghcr.io/developmentseed/tipg:latest]
  patterns:
    - "TiPG as standalone container — pure configuration, no custom code (D-06)"
    - "DATABASE_URL (not TIPG_DATABASE_URL) for TiPG DB connection (Pitfall #4)"
    - "TIPG_DB_SPATIAL_EXTENT=false when all geometries are NULL (Pitfall #6)"
    - "TIPG_MAX_FEATURES_PER_QUERY=10000 for DoS protection (T-02-05)"
    - "httpx.AsyncClient for integration tests against external service (not FastAPI TestClient)"

key-files:
  created:
    - apps/api/tests/test_tipg.py
  modified:
    - docker-compose.yml
    - .env.example
    - apps/api/uv.lock

key-decisions:
  - "TiPG health endpoint is /healthz (not /healthz.html as stated in RESEARCH.md) — verified against running container"
  - "TIPG_DB_SPATIAL_EXTENT=false required because all geometries are NULL in Phase 2 (Pitfall #6)"
  - "Integration tests use httpx.AsyncClient against port 8080, not FastAPI TestClient against port 8000"

patterns-established:
  - "Pattern: TiPG container config — DATABASE_URL env var, TIPG_* settings, healthcheck on /healthz, depends_on postgres service_healthy"
  - "Pattern: OGC API integration testing — httpx.AsyncClient to external service, @pytest.mark.integration marker, TIPG_URL module constant"

requirements-completed: [INT-01]

# Metrics
duration: 15min
completed: 2026-06-25
---

# Phase 2 Plan 03: OGC API for External GIS Clients Summary

**TiPG container serving OGC API Features/Tiles with CQL2 filtering and TileJSON for QGIS/ArcGIS integration, verified by 7 passing integration tests**

## Performance

- **Duration:** 15 min
- **Started:** 2026-06-25T22:01:36Z
- **Completed:** 2026-06-25T22:17:04Z
- **Tasks:** 2
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments
- TiPG container (ghcr.io/developmentseed/tipg:latest) added as 6th Docker Compose service on port 8080 with gunicorn+uvicorn workers
- TiPG auto-discovers the `public.structures` table and serves it as an OGC API Features collection with CQL2 filtering (INT-01)
- TileJSON endpoint at `/collections/public.structures/tiles/WebMercatorQuad/tilejson.json` ready for MapLibre consumption
- NULL geometry items return valid GeoJSON with `"geometry": null` (D-02, PostGIS 3.5.7 fix)
- 7 integration tests covering: collection discovery, GeoJSON items, CQL2 filtering, TileJSON, NULL geometry, pagination, and health check — all passing with 230 ingested structures
- DoS protection via TIPG_MAX_FEATURES_PER_QUERY=10000 (T-02-05 mitigation)

## Task Commits

Each task was committed atomically:

1. **Task 1: TiPG container configuration + .env.example** - `40faa68` (feat)
2. **Task 2: TiPG integration tests** - `634c0ea` (test)
3. **Fix: healthcheck endpoint + uv.lock** - `7dd18f4` (fix)

## Files Created/Modified
- `docker-compose.yml` - Added tipg service (image, DATABASE_URL, TIPG_* env vars, port 8080, healthcheck, depends_on postgres)
- `.env.example` - Added TiPG section: TIPG_CORS_ORIGIN, TIPG_DEFAULT_FEATURES_LIMIT, TIPG_MAX_FEATURES_PER_QUERY, TIPG_CATALOG_TTL, TIPG_DB_SPATIAL_EXTENT
- `apps/api/tests/test_tipg.py` - TestTiPGIntegration class with 7 @pytest.mark.integration tests using httpx.AsyncClient
- `apps/api/uv.lock` - Updated to include xlrd>=2.0.2 (was missing from lock file)

## Decisions Made
- TiPG health endpoint is `/healthz` (not `/healthz.html` as stated in RESEARCH.md) — discovered by testing all endpoints against the running container
- Used `TIPG_DB_SPATIAL_EXTENT=false` per Pitfall #6 — all geometries are NULL in Phase 2, ST_Extent returns NULL which can cause errors in /collections response
- Integration tests use `httpx.AsyncClient` against TiPG port 8080, not FastAPI TestClient against port 8000 — TiPG is a separate service

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TiPG healthcheck endpoint path**
- **Found during:** Task 1 verification (Docker health check failing)
- **Issue:** RESEARCH.md Pattern 3 and the plan specified `/healthz.html` as the TiPG health check endpoint. The actual TiPG image uses `/healthz` (without `.html` extension). The Docker healthcheck was failing with 404.
- **Fix:** Changed healthcheck URL in docker-compose.yml from `http://localhost:8080/healthz.html` to `http://localhost:8080/healthz`. Updated test_healthz in test_tipg.py to match.
- **Files modified:** docker-compose.yml, apps/api/tests/test_tipg.py
- **Verification:** `curl -s http://localhost:8080/healthz` returns 200, Docker healthcheck passes, test_healthz passes
- **Committed in:** 7dd18f4

**2. [Rule 3 - Blocking] Updated uv.lock to include xlrd dependency**
- **Found during:** Task 2 verification (API container startup failure)
- **Issue:** The `uv.lock` file was out of date — xlrd>=2.0.2 was added to pyproject.toml in Plan 01 but not to uv.lock. The Dockerfile uses `uv sync --frozen` which requires the lock file to be current. The API container failed with `ModuleNotFoundError: No module named 'xlrd'`.
- **Fix:** Ran `uv lock` to regenerate the lock file with xlrd included, then rebuilt API and celery-worker containers.
- **Files modified:** apps/api/uv.lock
- **Verification:** API container starts successfully, ingestion endpoint responds, 230 structures ingested
- **Committed in:** 7dd18f4

**3. [Rule 3 - Blocking] Applied Alembic migration 0002 and ran ingestion for test data**
- **Found during:** Task 2 verification (integration tests require ingested data)
- **Issue:** Migration 0002 from Plan 01 was not yet applied (geometry still NOT NULL), and no structures were ingested. Integration tests require data to verify items, CQL2 filtering, and NULL geometry handling.
- **Fix:** Applied migration via `API_SYNC_DATABASE_URL=postgresql+psycopg://ilarvne:yOv34H9W0E@localhost:5432/alemhackdb .venv/bin/alembic upgrade head`. Triggered ingestion via `POST /api/v1/ingestion/kazvodhoz`. 230 structures inserted.
- **Files modified:** None (database state change only)
- **Verification:** 230 structures in database, all 7 integration tests pass
- **Committed in:** N/A (database state change, not a code change)

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and test verification. The healthcheck fix is a factual correction (RESEARCH.md had wrong endpoint path). The uv.lock fix is a dependency sync issue from Plan 01. The migration/ingestion was required for test data. No scope creep.

## Issues Encountered
- Pre-existing test `test_fact_has_provenance` (integration test from Phase 1) fails when run from host because it tries to connect to `postgres` Docker hostname which is not resolvable outside the Docker network. This is a pre-existing issue unrelated to this plan's changes — the test is designed to run inside the Docker network.

## User Setup Required

None - no external service configuration required. TiPG is a self-contained Docker container that connects to the existing PostgreSQL instance via DATABASE_URL.

## Next Phase Readiness
- TiPG OGC API Features/Tiles endpoint is live at http://localhost:8080 — ready for QGIS/ArcGIS integration testing
- TileJSON endpoint ready for MapLibre frontend consumption (frontend workstream)
- CQL2 filtering verified on `type` column — additional filterable columns (district, water_source, technical_condition) available from migration 0002
- All geometries are NULL in Phase 2 — TiPG tiles will return empty tiles until Phase 4 assigns coordinates (expected per D-02)
- Manual QGIS verification recommended: Add Vector Layer → OGC API Features → URL: http://localhost:8080/collections/public.structures/items

## Self-Check: PASSED

- All 1 created file verified on disk: apps/api/tests/test_tipg.py
- All 3 task commits verified in git log: 40faa68, 634c0ea, 7dd18f4
- All 7 TiPG integration tests pass (with Docker stack running + 230 ingested structures)
- Full test suite: 39 passed, 2 skipped, 1 pre-existing failure (unrelated) — no regressions from this plan
- TiPG container healthy on port 8080 with correct /healthz healthcheck
- OGC API Features collection auto-discovery confirmed: public.structures in /collections response
- CQL2 filtering confirmed: filter=type='canal'&filter-lang=cql2-text returns filtered results
- TileJSON endpoint confirmed: /collections/public.structures/tiles/WebMercatorQuad/tilejson.json returns tile URL template
- NULL geometry confirmed: first feature has geometry: null (D-02, PostGIS 3.5.7 fix)

---
*Phase: 02-data-ingestion-spatial-api*
*Completed: 2026-06-25*
