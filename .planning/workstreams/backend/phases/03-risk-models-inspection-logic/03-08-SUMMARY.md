---
phase: 03-risk-models-inspection-logic
plan: 08
subsystem: risk
tags: [provenance, risk-engine, sqlalchemy, timezone, check-constraints, barrel-exports]

# Dependency graph
requires:
  - phase: 03-risk-models-inspection-logic
    provides: risk_engine with D-09 weak-evidence floor, ProvenanceModel, all ORM models
provides:
  - Provenance confidence wired to risk recomputation (D-09 floor now activates)
  - Complete model barrel exports for Alembic autogenerate
  - CheckConstraints on RiskAssessmentModel matching migration 0004
  - Timezone-aware datetime defaults across all model files
affects: [risk-api, alembic, provenance-tracking]

# Tech tracking
tech-stack:
  added: []
  patterns: [lambda-datetime-default-for-timezone-aware-columns, check-constraints-matching-migration]

key-files:
  created: []
  modified:
    - apps/api/src/api/services/risk_service.py
    - apps/api/src/api/models/__init__.py
    - apps/api/src/api/models/risk_assessment.py
    - apps/api/src/api/models/inspection.py
    - apps/api/src/api/models/document.py
    - apps/api/src/api/models/provenance.py
    - apps/api/src/api/models/structure.py

key-decisions:
  - "Used provenance.confidence_level if provenance else None (graceful degradation when provenance record missing)"
  - "CheckConstraint names match migration 0004 exactly (ck_risk_interval, ck_risk_repair_status)"
  - "user.py datetime.utcnow deferred to Plan 03-07 per plan scope"

patterns-established:
  - "Lambda defaults for timezone-aware columns: default=lambda: datetime.now(timezone.utc) instead of default=datetime.utcnow"

requirements-completed: [RISK-05]

# Metrics
duration: 2min
completed: 2026-06-26
---

# Phase 3 Plan 8: Provenance Confidence Wiring & Model Correctness Summary

**Wired provenance confidence into risk recomputation so D-09 weak-evidence floor activates for LOW-confidence structures; fixed model barrel exports, CheckConstraints, and timezone-aware datetime defaults**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-26T03:06:07Z
- **Completed:** 2026-06-26T03:08:21Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Closed BLOCKER gap: risk_service now loads ProvenanceModel and passes confidence_level to risk_engine, enabling the D-09 weak-evidence floor for LOW-confidence structures
- Added all Phase 3 models (RiskAssessmentModel, DocumentModel, InspectionModel, InspectionPhotoModel) to barrel exports so Alembic autogenerate discovers them
- Added __table_args__ with CheckConstraints on RiskAssessmentModel matching migration 0004
- Replaced all datetime.utcnow with timezone-aware datetime.now(timezone.utc) across 6 model files and risk_service

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire provenance confidence into risk recomputation production path** - `3334ae1` (feat)
2. **Task 2: Fix model barrel exports, CheckConstraints, and timezone-aware datetime defaults** - `dc61dde` (fix)

## Files Created/Modified
- `apps/api/src/api/services/risk_service.py` - Added ProvenanceModel query, wired confidence_level; fixed datetime.utcnow
- `apps/api/src/api/models/__init__.py` - Added RiskAssessmentModel, DocumentModel, InspectionModel, InspectionPhotoModel imports
- `apps/api/src/api/models/risk_assessment.py` - Added CheckConstraints, fixed datetime default
- `apps/api/src/api/models/inspection.py` - Fixed datetime defaults for both models
- `apps/api/src/api/models/document.py` - Fixed datetime default
- `apps/api/src/api/models/provenance.py` - Fixed datetime default
- `apps/api/src/api/models/structure.py` - Fixed datetime defaults (created_at, updated_at, valid_from)

## Decisions Made
- Used `provenance.confidence_level if provenance else None` for graceful degradation when provenance record is missing
- CheckConstraint names match migration 0004 exactly (ck_risk_interval, ck_risk_repair_status) to avoid Alembic drift
- user.py datetime.utcnow deferred to Plan 03-07 scope per plan instructions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed datetime.utcnow in risk_service.py**
- **Found during:** Task 2 (model correctness fixes)
- **Issue:** risk_service.py also used datetime.utcnow for assessment timestamps — same timezone bug as model files
- **Fix:** Changed two instances of `datetime.utcnow()` to `datetime.now(timezone.utc)` and added `timezone` to import
- **Files modified:** apps/api/src/api/services/risk_service.py
- **Verification:** grep confirms zero datetime.utcnow remaining in risk_service.py
- **Committed in:** dc61dde (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix — same category of bug as planned work, directly adjacent code. No scope creep.

## Issues Encountered
- test_provenance.py integration test fails due to missing PostgreSQL connection (pre-existing, requires Docker infrastructure). Not related to this plan's changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- D-09 weak-evidence floor now fully connected: LOW provenance → inspection_required floor activates
- All Phase 3 models registered on Base.metadata for Alembic autogenerate
- No remaining datetime.utcnow in models except user.py (Plan 03-07 scope)
- Ready for Plan 03-09

## Self-Check: PASSED

- All 7 modified files exist on disk
- Both commits (3334ae1, dc61dde) found in git log
- All plan-level verification commands pass
- 51 unit tests pass (risk_engine + risk_api)

---
*Phase: 03-risk-models-inspection-logic*
*Completed: 2026-06-26*
