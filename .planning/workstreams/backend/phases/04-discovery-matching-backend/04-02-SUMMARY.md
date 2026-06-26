---
phase: 04-discovery-matching-backend
plan: 02
subsystem: api, discovery, matching
tags: [osm, overpass, matching, postgis, pg_trgm, confidence, spatial]

requires:
  - phase: 04-01
    provides: CandidateModel, CandidateCreate schema, CandidateMatchResult schema, migration 0008

provides:
  - OSM Overpass discovery service with dedup
  - Hierarchical matching engine with spatial + name + attribute signals
  - Candidate CRUD + discover + review REST API endpoints
  - Confidence scoring with weighted formula

affects: [04-03, 04-04, frontend-map]

tech-stack:
  added: [httpx]
  patterns: [hierarchical matching, Overpass QL, confidence scoring]

key-files:
  created:
    - apps/api/src/api/services/discovery_service.py
    - apps/api/src/api/services/matching_service.py
    - apps/api/src/api/routes/candidates.py
    - apps/api/tests/test_discovery.py
    - apps/api/tests/test_matching.py
  modified: []

key-decisions:
  - "Used module-level function patching for route tests instead of DB session patching"
  - "Auto-registered candidates route via pkgutil discovery (no manual main.py edit needed)"
  - "ST_Transform to EPSG:3857 for metric distance in ST_DWithin queries"

patterns-established:
  - "DiscoveryService: Overpass QL → CandidateCreate → persist with provenance + dedup"
  - "MatchingService: spatial → name similarity → attribute comparison → confidence scoring"
  - "Route helper functions with direct DB access for candidate CRUD operations"

requirements-completed: []

duration: 4min
completed: 2026-06-26
---

# Phase 04 Plan 02: Discovery + Matching Summary

**OSM Overpass discovery service, hierarchical matching engine, and candidate CRUD endpoints**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-26T03:45:16Z
- **Completed:** 2026-06-26T03:49:39Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- OSM Overpass discovery pipeline: queries Overpass API, parses hydraulic structure elements, persists with provenance tracking and source_id dedup
- Hierarchical matching engine: spatial proximity (ST_DWithin 500m) → name similarity (pg_trgm) → attribute comparison, with weighted confidence scoring
- Candidate REST API: list, get, discover, review, delete endpoints with auth-gated operations
- Four-state match assignment per DISC-03: matched, likely_match, new_candidate, conflict
- 44 tests passing across discovery (27) and matching (17) test suites

## Task Commits

Each task was committed atomically:

1. **Task 1: OSM Overpass discovery service + candidate CRUD endpoints** - `6338d20` (feat)
2. **Task 2: Hierarchical matching engine** - `154e3e1` (feat)

## Files Created/Modified
- `apps/api/src/api/services/discovery_service.py` - OSM Overpass discovery with dedup and provenance
- `apps/api/src/api/services/matching_service.py` - Hierarchical matching engine with confidence scoring
- `apps/api/src/api/routes/candidates.py` - Candidate CRUD + discover + review REST endpoints
- `apps/api/tests/test_discovery.py` - 27 tests for discovery service and CRUD endpoints
- `apps/api/tests/test_matching.py` - 17 tests for confidence computation and match logic

## Decisions Made
- Used module-level function patching for route tests instead of DB session patching — simpler mock setup, matches existing test patterns
- Auto-registered candidates route via pkgutil discovery (no manual main.py edit needed) — consistent with all other routes
- ST_Transform to EPSG:3857 for metric distance in ST_DWithin queries — ensures accurate meter-based distance calculations

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed require_role missing Depends() wrapper**
- **Found during:** Task 1 (candidate routes)
- **Issue:** Used `require_role("engineer")` directly instead of `Depends(require_role("engineer"))` causing FastAPI to interpret the function as a response type
- **Fix:** Added `Depends()` wrapper to all three auth-gated endpoints
- **Files modified:** apps/api/src/api/routes/candidates.py
- **Verification:** All tests pass, no FastAPIError on app startup
- **Committed in:** 6338d20 (part of Task 1 commit)

**2. [Rule 1 - Bug] Fixed Overpass query test assertion format**
- **Found during:** Task 1 (discovery tests)
- **Issue:** Test checked for `waterway=canal` but actual query uses `"waterway"="canal"` format
- **Fix:** Updated test assertions to match the actual Overpass QL output format
- **Files modified:** apps/api/tests/test_discovery.py
- **Verification:** All 27 discovery tests pass
- **Committed in:** 6338d20 (part of Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both were quick fixes in the same task. No scope creep.

## Issues Encountered
None

## Next Phase Readiness
- Discovery pipeline ready for integration with matching workflow
- Matching engine ready for batch processing and human review workflow
- Next plan (04-03) can build the LangGraph review workflow on top of these services
- Consider adding matching endpoint POST /candidates/match-all to trigger batch matching

## Self-Check: PASSED

All 5 key files exist on disk. Both commits (6338d20, 154e3e1) found in git log. All 44 tests pass.

---
*Phase: 04-discovery-matching-backend*
*Completed: 2026-06-26*
