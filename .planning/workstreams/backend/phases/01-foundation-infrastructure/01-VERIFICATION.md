---
phase: 01-foundation-infrastructure
verified: 2026-06-25T21:12:00Z
status: passed
score: 12/12 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: lost
  previous_score: N/A
  note: "Previous VERIFICATION.md was lost during worktree-to-branch migration. This is a fresh verification after gap fixes (commit 11441ab). All human verification items resolved."
human_verification:
  - test: "Rebuild Docker containers with latest code and verify provenance/MinIO endpoints at runtime"
    expected: "After `docker compose up -d --build`, curl POST /api/v1/provenance returns 201, GET /api/v1/provenance returns 200, POST /api/v1/minio/presign returns 200 with presigned URL"
    why_human: "Running containers are stale (built from Plan 01-01 code only). Source code, tests, and DB schema are all verified correct, but the running API container returns 404 for provenance and MinIO routes because it lacks the services/, models/, and routes/ files added in Plan 02 and the gap fix commit."
    resolution: "RESOLVED — Containers rebuilt with `docker compose up -d --build`. All endpoints verified: POST /api/v1/provenance → 201, GET /api/v1/provenance → 200, timestamp range query → 200, POST /api/v1/minio/presign → 200 with presigned URL."
  - test: "Verify Celery health_check_task registration works at runtime after rebuild"
    expected: "After rebuild, `docker compose exec celery-worker python -c \"from api.celery_app import celery_app; print(celery_app.conf.include)\"` shows `('api.tasks.celery_tasks',)` and health_check_task.delay() returns a result"
    why_human: "Running celery-worker container has include=() (empty) — Gap Fix 1 (include=[\"api.tasks.celery_tasks\"]) is in source code but not in the stale container image."
    resolution: "RESOLVED — `docker compose exec celery-worker celery -A api.celery_app inspect registered` shows `api.tasks.celery_tasks.health_check_task` is registered."
  - test: "Consider updating docker-compose.yml API_SYNC_DATABASE_URL to postgresql+psycopg:// for consistency with Gap Fix 3"
    expected: "docker-compose.yml lines 68 and 95 use postgresql+psycopg:// instead of postgresql://, matching settings.py and .env.example"
    why_human: "Residual inconsistency: Gap Fix 3 changed settings.py and .env.example to use psycopg3 driver, but docker-compose.yml still uses postgresql:// (psycopg2). Non-blocking because Alembic is run from host with explicit env vars, but would fail if run inside the container."
    resolution: "RESOLVED — docker-compose.yml updated to use postgresql+psycopg:// for API_SYNC_DATABASE_URL on both api and celery-worker services."
---

# Phase 1: Foundation & Infrastructure Verification Report

**Phase Goal:** Running Docker stack with PostGIS schema, MinIO, Redis, and FastAPI skeleton with provenance tracking
**Verified:** 2026-06-25T21:07:56Z
**Status:** human_needed
**Re-verification:** Yes — fresh verification after gap fixes (previous VERIFICATION.md lost during worktree-to-branch migration)

## Verification Approach

Goal-backward verification starting from the 4 success criteria in ROADMAP.md, cross-referencing must_haves from PLAN frontmatter (01-01 and 01-02), and verifying all gap fixes (commit 11441ab). Evidence gathered via:
- Source code inspection (all key files read and verified)
- Test suite execution (17/17 tests pass)
- DB schema inspection (direct psql queries)
- Docker service health checks (docker compose ps)
- Behavioral spot-checks (curl against running API)
- Anti-pattern scanning (grep for debt markers, stubs, empty implementations)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Developer runs docker compose up -d and all 5 services report healthy within 60 seconds | VERIFIED | `docker compose ps` shows all 5 services (postgres, redis, minio, api, celery-worker) as "Up (healthy)" |
| 2 | GET /health/live returns 200 with {"status": "ok"} | VERIFIED | `curl http://localhost:8000/health/live` returns 200 `{"status":"ok"}` |
| 3 | GET /health/ready returns 200 with status=healthy and checks for postgres, redis, minio all ok | VERIFIED | `curl http://localhost:8000/health/ready` returns 200 `{"status":"healthy","checks":{"postgres":{"status":"ok"},"redis":{"status":"ok"},"minio":{"status":"ok"}}}` |
| 4 | GET /health/ready returns 503 when any service is down | VERIFIED | Tests test_health_ready_db_down, test_health_ready_redis_down, test_health_ready_minio_down all pass (17/17 suite) |
| 5 | Celery worker processes health_check_task and returns a result via Redis | VERIFIED (source) | Source code: celery_app.py has `include=["api.tasks.celery_tasks"]` (Gap Fix 1), celery_tasks.py defines `health_check_task`. Running container responds to `celery inspect ping` (OK/pong). NOTE: running container has stale include=() — see Human Verification. |
| 6 | Developer creates a provenance record via POST /api/v1/provenance and retrieves it via GET /api/v1/provenance/{id} | VERIFIED (source+test) | Source: provenance.py route has POST (201) + GET by id (200/404). Test: test_create_provenance and test_get_provenance_by_id pass. NOTE: running container returns 404 (stale image) — see Human Verification. |
| 7 | Developer queries provenance by source_type, confidence_level, and timestamp range via GET /api/v1/provenance | VERIFIED (source+test) | Source: provenance.py route has source_type, confidence_level, recorded_after, recorded_before params (Gap Fix 2). Service: query_provenance has where filters for all 4. Test: test_query_provenance_by_source_type, test_query_provenance_by_confidence, test_query_provenance_by_timestamp_range all pass. |
| 8 | Developer generates a presigned upload URL via POST /api/v1/minio/presign and download URL via GET /api/v1/minio/presign/{object_name} | VERIFIED (source+test) | Source: minio.py route has POST /presign + GET /presign/{object_name:path}. Test: test_presign_upload, test_presign_download, test_presigned_roundtrip all pass. |
| 9 | Structure features are stored in PostGIS with Geometry(Point, srid=4326) — no binary data in PostgreSQL | VERIFIED | DB: `\d structures` shows `geometry(Point,4326)` column, GiST spatial index. `information_schema.columns` query returns 0 binary columns (bytea/oid/blob). Tests: test_geometry_in_postgis, test_no_binary_in_postgis pass. |
| 10 | Imagery evidence is stored in MinIO buckets (sujoly-imagery, sujoly-documents, sujoly-photos) — separate from PostGIS | VERIFIED | `mc ls local/` shows 3 buckets: sujoly-documents, sujoly-imagery, sujoly-photos. main.py lifespan creates all 3 on startup. |
| 11 | Every structure record has a provenance_id foreign key referencing the provenance table | VERIFIED | DB: `\d structures` shows `structures_provenance_id_fkey FOREIGN KEY (provenance_id) REFERENCES provenance(id)` with `not null`. Model: structure.py line 38-39 `ForeignKey("provenance.id"), nullable=False`. |
| 12 | Every structure fact has its own provenance_id foreign key — facts are individually traceable | VERIFIED | DB: `\d structure_facts` shows `structure_facts_provenance_id_fkey FOREIGN KEY (provenance_id) REFERENCES provenance(id)` with `not null`. Test: test_fact_has_provenance passes (IntegrityError on missing provenance_id). |

**Score:** 12/12 truths verified

All truths are verified through source code inspection, test suite execution (17/17 pass), and direct DB schema queries. Three truths (5, 6, 8) have runtime behavioral spot-check failures against the running container due to stale Docker images — see Human Verification section.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docker-compose.yml` | 5-service stack with health checks | VERIFIED | 5 services defined with `service_healthy` conditions, health checks for all services. MinIO uses `mc ready local`, postgres checks postgis extension, celery uses `celery inspect ping`. |
| `docker/postgres/Dockerfile` | Custom postgis+pgvector image | VERIFIED | DB has postgis, vector, pg_trgm extensions installed (confirmed via `pg_extension` query). |
| `apps/api/src/api/main.py` | FastAPI app with lifespan, route registration | VERIFIED | Lifespan initializes MinIOService + buckets. Routes: health, provenance, minio all registered (lines 124-126). Security headers, CORS, global exception handler present. |
| `apps/api/src/api/routes/health.py` | Health check endpoints (live + ready) | VERIFIED | /health/live returns {"status":"ok"}, /health/ready probes postgres/redis/minio. 5 tests pass. |
| `apps/api/src/api/config/settings.py` | Pydantic Settings with local Docker defaults | VERIFIED | env_prefix="API_", psycopg3 driver (`postgresql+psycopg://` line 34, Gap Fix 3), local Docker defaults (not alem.ai). |
| `apps/api/src/api/infrastructure/database.py` | SQLAlchemy async engine and session factory | VERIFIED | Used by all services and tests. async_session() pattern confirmed in provenance_service.py. |
| `apps/api/src/api/celery_app.py` | Celery app with Redis broker | VERIFIED | `include=["api.tasks.celery_tasks"]` present (Gap Fix 1, line 11). broker=settings.redis_url. |
| `apps/api/src/api/models/provenance.py` | ProvenanceModel ORM | VERIFIED | `__tablename__ = "provenance"`, source_type (indexed), confidence_level (check constraint), recorded_at. Mapped + mapped_column style. |
| `apps/api/src/api/models/structure.py` | StructureModel + StructureFactModel | VERIFIED | Geometry("Point", srid=4326), ForeignKey("provenance.id") on both models, JSONB attribute_value. No legacy Column(). |
| `apps/api/src/api/services/minio_client.py` | MinIOService | VERIFIED | ensure_bucket, presigned_upload_url (presigned_put_object, 1hr), presigned_download_url (presigned_get_object, 2hr). |
| `apps/api/src/api/services/provenance_service.py` | Provenance CRUD service | VERIFIED | create_provenance, get_provenance, query_provenance (with recorded_after/recorded_before where filters, Gap Fix 2). |
| `apps/api/src/api/routes/provenance.py` | Provenance REST endpoints | VERIFIED | POST /provenance (201), GET /provenance/{id} (200/404), GET /provenance with source_type/confidence_level/recorded_after/recorded_before filters. |
| `apps/api/src/api/routes/minio.py` | MinIO presigned URL endpoints | VERIFIED | POST /presign, GET /presign/{object_name:path}, uses request.app.state.minio. |
| `apps/api/alembic/versions/0001_initial.py` | Initial migration | VERIFIED | Creates provenance, structures, structure_facts tables with FKs, GiST spatial index, check constraint. Drop in reverse order. |
| `apps/api/alembic/env.py` | Alembic env with GeoAlchemy2 helpers | VERIFIED | alembic_helpers.include_object/writer/render_item, custom include_object for PostGIS extension tables, target_metadata=Base.metadata, settings.sync_database_url. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| main.py | routes/health.py | `app.include_router(health.router)` | WIRED | Line 124. Verified: /health/live and /health/ready respond on running container. |
| main.py | routes/provenance.py | `app.include_router(provenance.router)` | WIRED (source) | Line 125. Source code confirmed. Running container lacks this (stale image). |
| main.py | routes/minio.py | `app.include_router(minio.router)` | WIRED (source) | Line 126. Source code confirmed. Running container lacks this (stale image). |
| routes/provenance.py | services/provenance_service.py | service function calls | WIRED | Imports create_provenance, get_provenance, query_provenance. Route calls all three. |
| routes/minio.py | services/minio_client.py | `request.app.state.minio` | WIRED | Line 38: `minio_service = request.app.state.minio`. main.py lifespan sets app.state.minio. |
| models/structure.py | models/provenance.py | `ForeignKey("provenance.id")` | WIRED | Both StructureModel (line 38) and StructureFactModel (line 68) have FK to provenance.id. DB confirms FK constraints. |
| docker-compose.yml | apps/api/Dockerfile | `context: ./apps/api` | WIRED | Lines 63, 91. Both api and celery-worker build from ./apps/api. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| routes/provenance.py | ProvenanceResponse | provenance_service.py → async_session → ProvenanceModel | Yes (DB query via SQLAlchemy select) | FLOWING |
| routes/minio.py | PresignResponse | app.state.minio → MinIOService → Minio SDK | Yes (presigned_put_object/presigned_get_object) | FLOWING |
| routes/health.py | HealthStatus | async_session (DB), Redis.from_url (Redis), Minio (MinIO) | Yes (real infrastructure probes) | FLOWING |
| models/structure.py | geometry | Geometry("Point", srid=4326) column | Yes (PostGIS spatial type in DB) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Health liveness | `curl http://localhost:8000/health/live` | 200 `{"status":"ok"}` | PASS |
| Health readiness | `curl http://localhost:8000/health/ready` | 200 all checks ok | PASS |
| POST provenance | `curl -X POST http://localhost:8000/api/v1/provenance ...` | 404 `{"detail":"Not Found"}` | FAIL (stale container) |
| GET provenance list | `curl http://localhost:8000/api/v1/provenance` | 404 `{"detail":"Not Found"}` | FAIL (stale container) |
| GET provenance timestamp range | `curl "http://localhost:8000/api/v1/provenance?recorded_after=...&recorded_before=..."` | 404 `{"detail":"Not Found"}` | FAIL (stale container) |
| POST MinIO presign | `curl -X POST http://localhost:8000/api/v1/minio/presign ...` | 404 `{"detail":"Not Found"}` | FAIL (stale container) |
| Celery worker ping | `docker compose exec celery-worker celery -A api.celery_app inspect ping` | OK/pong | PASS |
| Celery task registration | `docker compose exec celery-worker python -c "..."` | include=() (empty) | FAIL (stale container) |
| Full test suite | `uv run pytest tests/ -x -v` | 17 passed | PASS |
| DB schema: structures geometry | `psql ... \d structures` | geometry(Point,4326) column exists | PASS |
| DB schema: no binary columns | `psql ... SELECT ... WHERE data_type IN ('bytea','oid','blob')` | 0 rows | PASS |
| PostGIS extensions | `psql ... SELECT extname FROM pg_extension` | postgis, vector, pg_trgm | PASS |
| MinIO buckets | `mc ls local/` | sujoly-documents, sujoly-imagery, sujoly-photos | PASS |

**Note:** The 5 FAIL results are all caused by stale Docker containers (built from Plan 01-01 code, before Plan 02 route wiring and gap fixes). The source code, tests, and DB schema are all correct. Rebuilding the containers (`docker compose up -d --build`) would resolve all runtime failures.

### Probe Execution

No conventional probe scripts (`scripts/*/tests/probe-*.sh`) found for this phase. The test suite (`uv run pytest tests/ -x -v`) serves as the probe — 17/17 PASS.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-07 | 01-02 | Every fact and status on every structure has a provenance record (source type, source reference, confidence level, timestamp, contributor) | SATISFIED | ProvenanceModel with all 5 fields. provenance_id FK (nullable=False) on both StructureModel and StructureFactModel. CRUD API with source_type/confidence_level/timestamp range query (Gap Fix 2). test_fact_has_provenance proves FK enforcement. DB schema confirms FK constraints + check constraint on confidence_level. |
| INT-04 | 01-01, 01-02 | System separates imagery evidence (STAC/COG in MinIO) from structure features (PostGIS) | SATISFIED | structures table has Geometry(Point,4326) in PostGIS, no binary columns. MinIO has 3 buckets (sujoly-imagery, sujoly-documents, sujoly-photos). test_geometry_in_postgis and test_no_binary_in_postgis pass. REQUIREMENTS.md marks both as [x] Complete. |

### Gap Fix Verification

| Gap Fix | Description | Source Code | Test | Runtime | Status |
|---------|-------------|-------------|------|---------|--------|
| Gap 1 | Celery task registration: `include=["api.tasks.celery_tasks"]` in Celery constructor | VERIFIED (celery_app.py line 11) | N/A (no specific test) | FAIL (running container has include=()) | VERIFIED (source) — needs container rebuild |
| Gap 2 | Provenance timestamp range: `recorded_after`/`recorded_before` params in route + service | VERIFIED (route lines 96-97, service lines 76-77 + 102-105) | PASS (test_query_provenance_by_timestamp_range) | FAIL (running container 404) | VERIFIED (source+test) — needs container rebuild |
| Gap 3 | Psycopg3 driver: `postgresql+psycopg://` in settings + .env.example | VERIFIED (settings.py line 34, .env.example) | PASS (Alembic + tests use psycopg3) | WARNING (docker-compose.yml lines 68, 95 still use `postgresql://`) | VERIFIED (source) — docker-compose.yml residual inconsistency |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| docker-compose.yml | 68, 95 | `API_SYNC_DATABASE_URL: postgresql://` (psycopg2 driver, not psycopg3) | WARNING | Alembic would fail if run inside container (psycopg2 not installed). Non-blocking: Alembic is run from host with explicit env vars. Inconsistent with Gap Fix 3. |

No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers found in any source files.
No empty implementations (return null/[]{}/{}) found in source files.
No hardcoded empty data found in source files.

### Human Verification Required

### 1. Rebuild Docker Containers and Verify Endpoints at Runtime

**Test:** Run `docker compose up -d --build` to rebuild containers with latest code, then test:
- `curl -X POST http://localhost:8000/api/v1/provenance -H "Content-Type: application/json" -d '{"source_type":"kazvodhoz_spreadsheet","confidence_level":"HIGH"}'` — expect 201
- `curl http://localhost:8000/api/v1/provenance` — expect 200 with list
- `curl "http://localhost:8000/api/v1/provenance?recorded_after=2026-01-01T00:00:00Z&recorded_before=2026-12-31T23:59:59Z"` — expect 200 (timestamp range query)
- `curl -X POST http://localhost:8000/api/v1/minio/presign -H "Content-Type: application/json" -d '{"bucket":"sujoly-documents","object_name":"test/file.pdf"}'` — expect 200 with presigned URL

**Expected:** All endpoints return expected status codes (201/200) with correct response bodies.
**Why human:** The running API and celery-worker containers are stale (built from Plan 01-01 code only). Source code, tests (17/17 pass), and DB schema are all verified correct. The containers need rebuilding to include Plan 02 route wiring and gap fix commit 11441ab. The verifier must not modify state (rebuild containers) per behavioral spot-check constraints.

### 2. Verify Celery Task Registration at Runtime After Rebuild

**Test:** After rebuild, run:
- `docker compose exec celery-worker python -c "from api.celery_app import celery_app; print(celery_app.conf.include)"` — expect `('api.tasks.celery_tasks',)`
- `docker compose exec celery-worker python -c "from api.celery_app import celery_app; print('health_check_task' in celery_app.tasks)"` — expect `True`

**Expected:** Celery include list contains `api.tasks.celery_tasks` and `health_check_task` is registered.
**Why human:** Gap Fix 1 added `include=["api.tasks.celery_tasks"]` to source code (verified), but the running container has `include=()` (stale image). Cannot verify at runtime without rebuilding.

### 3. Update docker-compose.yml API_SYNC_DATABASE_URL (Optional)

**Test:** Change docker-compose.yml lines 68 and 95 from `postgresql://` to `postgresql+psycopg://` for consistency with Gap Fix 3.
**Expected:** `API_SYNC_DATABASE_URL: postgresql+psycopg://...` matching settings.py and .env.example.
**Why human:** Residual inconsistency from Gap Fix 3. Non-blocking (Alembic runs from host, not container), but should be fixed for consistency. This is a code change, not just a deployment step.

### Gaps Summary

No code-level gaps found. All 12 observable truths are verified through source code inspection, test suite execution (17/17 pass), and direct DB schema queries. All 3 gap fixes are applied in the source code and verified.

**The single issue is deployment-state, not code-state:** The running Docker containers (api, celery-worker) are stale — built from Plan 01-01 code only, before Plan 02 route wiring (commit b000d48) and gap fixes (commit 11441ab). The containers lack:
- Provenance routes (`/api/v1/provenance` returns 404)
- MinIO presign routes (`/api/v1/minio/presign` returns 404)
- Services/ and models/ directories
- Celery `include` parameter (empty tuple, health_check_task not registered)

**Fix:** `docker compose up -d --build` rebuilds both containers with the latest code. All runtime behavioral failures would resolve.

**Minor residual:** docker-compose.yml lines 68 and 95 still use `postgresql://` (psycopg2) for `API_SYNC_DATABASE_URL` instead of `postgresql+psycopg://` (psycopg3). This is inconsistent with Gap Fix 3 but non-blocking (Alembic runs from host with explicit env vars).

---

_Verified: 2026-06-25T21:07:56Z_
_Verifier: the agent (gsd-verifier)_
