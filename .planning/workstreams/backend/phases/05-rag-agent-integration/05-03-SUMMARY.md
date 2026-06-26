---
phase: 05-rag-agent-integration
plan: 03
subsystem: api, search, embeddings
tags: [pgvector, embeddings, celery, alem-api, httpx, vector-search]

# Dependency graph
requires:
  - phase: 05-01
    provides: EmbeddingModel ORM + embeddings table migration + search_service scaffold
  - phase: 05-02
    provides: LLM config in settings.py (Alem API pattern)
provides:
  - EmbeddingService with real Alem text-1024 API integration
  - Celery embedding tasks (generate_structure, generate_all)
  - Auto-embedding triggers on structure/inspection/document creation
  - _vector_search powered by real embeddings
affects: [search_service, structure_service, inspection_service]

# Tech tracking
tech-stack:
  added: [httpx embedding API calls, Alem text-1024 model integration]
  patterns: [embedding-service-with-fallback, auto-embedding-celery-triggers, hash-based-pseudo-embedding-fallback]

key-files:
  created:
    - apps/api/src/api/services/embedding_service.py
    - apps/api/tests/test_embedding.py
  modified:
    - apps/api/src/api/models/embedding.py
    - apps/api/src/api/config/settings.py
    - apps/api/src/api/tasks/celery_tasks.py
    - apps/api/src/api/services/structure_service.py
    - apps/api/src/api/services/inspection_service.py
    - apps/api/src/api/services/search_service.py
    - apps/api/alembic/versions/0009_embeddings.py
    - apps/api/tests/test_search.py

key-decisions:
  - "Real Alem text-1024 API embeddings (1024-dim) instead of pseudo-embeddings per user directive"
  - "Vector(1024) instead of Vector(1536) to match Alem text-1024 model output"
  - "Deterministic hash-based pseudo-embedding fallback when API key unavailable"
  - "Late imports in Celery tasks matching project pattern for clean test patching"
  - "Auto-embedding dispatch via try/except pattern matching risk recomputation triggers"

patterns-established:
  - "Embedding service with API fallback: real API → pseudo-embed on failure"
  - "Celery embedding dispatch: try/except with logger.warning on failure, matches D-05 pattern"

requirements-completed: []

# Metrics
duration: 4min
completed: 2026-06-26
---

# Phase 5 Plan 3: Embedding Service Summary

**Real Alem text-1024 embedding service (1024-dim) with Celery tasks and auto-embedding triggers on data creation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-26T04:22:00Z
- **Completed:** 2026-06-26T04:26:16Z
- **Tasks:** 1
- **Files modified:** 10

## Accomplishments
- EmbeddingService with real Alem text-1024 API via httpx (POST /v1/embeddings)
- Deterministic hash-based pseudo-embedding fallback when API key unavailable
- Updated EmbeddingModel from Vector(1536) → Vector(1024) to match Alem model
- Updated migration 0009 from vector(1536) → vector(1024)
- embed_structure, embed_inspection, embed_document methods with text concatenation
- Batch embedding methods: embed_all_structures, embed_all_inspections
- Celery tasks: embeddings.generate_structure, embeddings.generate_all
- Auto-embedding triggers on structure/inspection/document creation
- _vector_search in SearchService now uses real embeddings via EmbeddingService
- 14 new embedding tests + updated search tests (301 total passing)

## Task Commits

1. **Task 1: Embedding service and Celery embedding task** - `fcf8cc7` (feat)

## Files Created/Modified
- `apps/api/src/api/services/embedding_service.py` - EmbeddingService with Alem API + pseudo-embedding fallback
- `apps/api/tests/test_embedding.py` - 14 tests for embedding service and Celery tasks
- `apps/api/src/api/models/embedding.py` - Updated Vector(1536) → Vector(1024)
- `apps/api/src/api/config/settings.py` - Added embedding_base_url, embedding_model, embedding_api_key, embedding_dimensions
- `apps/api/src/api/tasks/celery_tasks.py` - Added generate_structure_embedding, generate_all_embeddings Celery tasks
- `apps/api/src/api/services/structure_service.py` - Auto-embedding dispatch on structure creation
- `apps/api/src/api/services/inspection_service.py` - Auto-embedding dispatch on inspection creation
- `apps/api/src/api/services/search_service.py` - _vector_search uses real embeddings via EmbeddingService
- `apps/api/alembic/versions/0009_embeddings.py` - Updated vector(1536) → vector(1024)
- `apps/api/tests/test_search.py` - Updated vector search tests for real embedding pipeline

## Decisions Made
- Used real Alem text-1024 API embeddings per user directive instead of pseudo-embeddings in plan
- Changed Vector(1536) → Vector(1024) to match Alem text-1024 model output dimensions
- Kept deterministic pseudo-embedding as fallback so pipeline works without API key
- Followed existing try/except + logger.warning pattern for Celery dispatch (matches D-05 risk triggers)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Real Alem API embeddings instead of pseudo-embeddings**
- **Found during:** Task 1 (embedding service implementation)
- **Issue:** Plan specified pseudo-embeddings (hash-based), but user directive explicitly requires "REAL embedding models configured via .env"
- **Fix:** Implemented real Alem text-1024 API calls via httpx with pseudo-embedding as fallback only
- **Files modified:** apps/api/src/api/services/embedding_service.py
- **Verification:** 14 tests pass including test_embed_text_calls_real_api_with_key
- **Committed in:** fcf8cc7 (part of task commit)

**2. [Rule 1 - Bug] Vector dimension mismatch: 1536 vs 1024**
- **Found during:** Task 1 (reading existing EmbeddingModel)
- **Issue:** EmbeddingModel used Vector(1536) for OpenAI ada-002 but Alem text-1024 produces 1024-dim vectors. Mismatch would cause data corruption.
- **Fix:** Updated EmbeddingModel to Vector(1024) and migration 0009 from vector(1536) to vector(1024)
- **Files modified:** apps/api/src/api/models/embedding.py, apps/api/alembic/versions/0009_embeddings.py
- **Verification:** Test test_embed_text_produces_1024_dim_vector passes
- **Committed in:** fcf8cc7 (part of task commit)

**3. [Rule 1 - Bug] Search test assumed empty vector search**
- **Found during:** Task 1 (running test suite)
- **Issue:** test_vector_search_returns_empty_for_mvp expected _vector_search to return empty list, but it now uses real embeddings
- **Fix:** Updated test to mock embedding service and verify vector search returns results with embeddings
- **Files modified:** apps/api/tests/test_search.py
- **Verification:** All 12 search tests pass
- **Committed in:** fcf8cc7 (part of task commit)

---

**Total deviations:** 3 auto-fixed (1 missing critical, 2 bugs)
**Impact on plan:** All auto-fixes necessary for correctness and user directive compliance. No scope creep.

## Issues Encountered
- Pre-existing integration test `test_provenance.py::test_fact_has_provenance` fails without Docker DB (out of scope — not caused by this plan's changes)

## Next Phase Readiness
- Embedding pipeline complete — hybrid search now works with real vector embeddings
- Ready for full end-to-end testing with Docker Compose stack
- Phase 05 is complete (all 3 plans done)

---
*Phase: 05-rag-agent-integration*
*Completed: 2026-06-26*

## Self-Check: PASSED

- All 10 key files verified present on disk
- feat(05-03) commit fcf8cc7 found in git log
- 14/14 embedding tests passing
- 301/301 unit tests passing (excluding integration tests requiring Docker DB)
