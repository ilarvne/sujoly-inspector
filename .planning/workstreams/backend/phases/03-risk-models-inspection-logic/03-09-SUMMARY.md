---
phase: 03-risk-models-inspection-logic
plan: 09
subsystem: api
tags: [docker, geojson, csv, minio, security, cross-structure, export, inspection]

# Dependency graph
requires:
  - phase: 03-risk-models-inspection-logic
    provides: Export service, inspection routes, Dockerfile
provides:
  - Docker templates copy for PDF export in runtime image
  - GeoJSON geometry serialization as JSON-compatible dict
  - Lang-aware CSV name column with fallback
  - MinIO connection management via context manager
  - Inspection structure_id ownership verification
affects: [export-service, inspection-routes, docker-build]

# Tech tracking
tech-stack:
  added: [geoalchemy2.shape.to_shape, shapely .geojson]
  patterns: [context manager for HTTP connection lifecycle, ownership verification on nested resource endpoints]

key-files:
  created: []
  modified:
    - apps/api/Dockerfile
    - apps/api/src/api/services/export_service.py
    - apps/api/src/api/routes/inspections.py
    - apps/api/tests/test_inspections.py

key-decisions:
  - "Used to_shape + shapely .geojson for GeoJSON serialization instead of raw WKB"
  - "Return 404 (not 403) on structure_id mismatch to avoid disclosing inspection existence in another structure"
  - "Lang-aware CSV name uses or-chain fallback: name_{lang} or name_ru"

patterns-established:
  - "Context manager pattern for MinIO get_object — always use `with` statement for HTTP response objects"
  - "Ownership verification on nested resource endpoints — verify parent resource ID matches path parameter"

requirements-completed: [RISK-08, DATA-05]

# Metrics
duration: 4min
completed: 2026-06-26
---

# Phase 03 Plan 09: Fix PDF Export, Export Service Correctness, and Inspection Disclosure Summary

**Fix Docker templates copy, GeoJSON WKB serialization, CSV lang-aware name, MinIO connection leak, and cross-structure inspection disclosure**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-26T03:11:03Z
- **Completed:** 2026-06-26T03:15:14Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- PDF export now works in Docker runtime — templates directory included in image
- GeoJSON export produces JSON-serializable geometry dicts (type + coordinates) instead of raw WKB objects
- CSV export uses lang-aware name column (name_kk for kk, name_en for en, name_ru for ru) with fallback
- MinIO HTTP connections properly managed via context manager — no connection leaks on exceptions
- Inspection detail endpoint verifies structure_id ownership — cross-structure disclosure returns 404

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix Dockerfile templates copy and export_service GeoJSON/CSV/MinIO issues** - `0f36085` (fix)
2. **Task 2: Fix inspection detail endpoint to verify structure_id ownership** - `2a96cb0` (fix)

## Files Created/Modified
- `apps/api/Dockerfile` - Added COPY --from=builder /app/templates /app/templates in runtime stage
- `apps/api/src/api/services/export_service.py` - Fixed GeoJSON geometry serialization, CSV lang-aware name, MinIO context manager
- `apps/api/src/api/routes/inspections.py` - Added structure_id ownership verification on detail endpoint
- `apps/api/tests/test_inspections.py` - Added test for cross-structure access returning 404

## Decisions Made
- Used to_shape + shapely .geojson for GeoJSON serialization — simplest approach that produces a proper GeoJSON dict without requiring ST_AsGeoJSON SQL calls
- Return 404 (not 403) on structure_id mismatch — avoids disclosing that an inspection exists in another structure (T-03-09a mitigation)
- Lang-aware CSV name uses or-chain: `getattr(struct, f"name_{lang}", None) or getattr(struct, "name_ru", "")` — falls back to Russian when the lang-specific name is None

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All export and inspection correctness issues resolved
- All 20 tests pass (10 exports + 10 inspections)
- Ready for next plan in Phase 03

## Self-Check: PASSED

- All 4 modified files exist on disk
- Both 03-09 commits found in git log
- All 20 tests pass (test_exports.py + test_inspections.py)

---
*Phase: 03-risk-models-inspection-logic*
*Completed: 2026-06-26*
