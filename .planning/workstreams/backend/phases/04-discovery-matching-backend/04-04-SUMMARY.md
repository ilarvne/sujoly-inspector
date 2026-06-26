---
phase: 04-discovery-matching-backend
plan: 04
subsystem: api, discovery, matching
tags: [celery, discovery, matching, pipeline, fastapi, postgis]

# Dependency graph
requires:
  - phase: 04-discovery-matching-backend
    provides: CandidateModel, MatchingService, DiscoveryService, candidate CRUD endpoints
provides:
  - Celery run_discovery_pipeline task (discover→match→score)
  - discover_and_match method for auto-matching on discovery
  - POST /candidates/match endpoint (batch matching)
  - POST /candidates/{id}/match endpoint (single candidate matching)
affects: [04-discovery-matching-backend, celery-tasks, candidate-routes]

# Tech tracking
tech-stack:
  added: []
  patterns: [celery-async-pipeline, late-import-for-testability, asyncio-run-bridge]

key-files:
  created: []
  modified:
    - apps/api/src/api/tasks/celery_tasks.py
    - apps/api/src/api/services/discovery_service.py
    - apps/api/src/api/routes/candidates.py
    - apps/api/tests/test_discovery.py

key-decisions:
  - "Late imports in Celery task (from api.services import inside function) to avoid circular deps and enable test patching at source module"
  - "discover_and_match is a separate method from discover_candidates to preserve backward compatibility of the simpler discover path"
  - "Match endpoints use late import of MatchingService matching existing route pattern for service imports"
  - "asyncio.run() bridges async service calls from sync Celery task — same pattern as recompute_structure_risk"

patterns-established:
  - "Celery pipeline task pattern: late import services → asyncio.run() bridge → loop over candidates → update in DB"
  - "Route late-import pattern for services: import inside handler function for clean mock patching at source module"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-06-26
---

# Phase 04 Plan 04: Discovery+Matching Pipeline Summary

**Celery discover→match pipeline with auto-matching on discovery and manual match endpoints**

## Performance

- **Duration:** 3 min
- **Started:** 2026-06-26T03:57:55Z
- **Completed:** 2026-06-26T04:00:59Z
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments
- Added `run_discovery_pipeline` Celery task that discovers candidates from OSM, auto-matches each against the registry, and returns a summary with match status counts
- Added `discover_and_match` method to DiscoveryService for integrated discovery+matching (backward compatible with existing `discover_candidates`)
- Added POST `/candidates/match` endpoint for batch matching of all unmatched candidates
- Added POST `/candidates/{id}/match` endpoint for single candidate matching with DB update
- All 52 tests pass (discovery + matching test suites)

## Task Commits

Each task was committed atomically:

1. **Task 1: Celery discovery+matching pipeline and match endpoint** - `adc40a0` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `apps/api/src/api/tasks/celery_tasks.py` - Added `run_discovery_pipeline` Celery task with asyncio.run() bridge
- `apps/api/src/api/services/discovery_service.py` - Added `discover_and_match` method and CandidateMatchResult import
- `apps/api/src/api/routes/candidates.py` - Added POST /candidates/match and POST /candidates/{id}/match endpoints
- `apps/api/tests/test_discovery.py` - Added tests for pipeline, discover_and_match, match endpoints, and Celery task

## Decisions Made
- Late imports in Celery task and route handlers for clean test patching at source module level (avoids AttributeError on patch)
- `discover_and_match` is a separate method from `discover_candidates` to preserve backward compatibility
- `asyncio.run()` bridge pattern used consistently across all Celery tasks for async service calls
- Match endpoints use module-level `_get_candidate_by_id` helper for consistency with existing route helpers

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed mock patch targets for late imports**
- **Found during:** Task 1 (test execution)
- **Issue:** Tests initially patched `api.routes.candidates.MatchingService` and `api.tasks.celery_tasks.DiscoveryService` but these modules use late imports inside function bodies, so the patch targets don't exist at module level
- **Fix:** Changed patch targets to `api.services.matching_service.MatchingService` and `api.services.discovery_service.DiscoveryService` (the source modules where the classes are defined)
- **Files modified:** apps/api/tests/test_discovery.py
- **Verification:** All 52 tests pass
- **Committed in:** adc40a0 (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary fix for test patching with late-import pattern. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Discovery+matching pipeline is fully wired: Celery task, auto-matching on discovery, manual match endpoints
- Phase 04 complete — all 4 plans done (CandidateModel, MatchingService, DiscoveryService, Pipeline integration)
- Ready for next phase or verification

## Self-Check: PASSED

- All 4 modified files exist on disk
- Commit adc40a0 found in git log
- All 52 tests pass (test_discovery.py + test_matching.py)

---
*Phase: 04-discovery-matching-backend*
*Completed: 2026-06-26*
