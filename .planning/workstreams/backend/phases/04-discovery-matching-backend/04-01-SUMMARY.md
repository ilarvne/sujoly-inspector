---
phase: 04-discovery-matching-backend
plan: 01
subsystem: database
tags: [candidates, matching, postgis, pg_trgm, alembic, sqlalchemy, pydantic]

# Dependency graph
requires:
  - phase: 03-data-quality-risk
    provides: structures, provenance, users tables and ORM models
provides:
  - CandidateModel ORM model for discovered hydraulic structure candidates
  - Migration 0008 with pg_trgm extension and candidates table
  - Pydantic schemas for candidate CRUD, review, and match result
  - Tests for model creation, CheckConstraints, and schema validation
affects: [04-02, 04-03, 04-04, discovery, matching, review]

# Tech tracking
tech-stack:
  added: [pg_trgm]
  patterns: [candidate-matching-state-machine, evidence-jsonb, confidence-scoring]

key-files:
  created:
    - apps/api/src/api/models/candidate.py
    - apps/api/alembic/versions/0008_candidates.py
    - apps/api/src/api/schemas/candidates.py
    - apps/api/tests/test_candidates.py
  modified:
    - apps/api/src/api/models/__init__.py

key-decisions:
  - "ORM-level defaults (match_status, confidence) are SQL INSERT defaults, not Python constructor defaults — service layer must set them explicitly"
  - "Migration 0008 branches from 0006 (inspections merge migration) as the latest in the chain"

patterns-established:
  - "CandidateModel: match_status state machine (unmatched→matched/likely_match/new_candidate/conflict/rejected)"
  - "Evidence JSONB: dict of evidence sources with similarity scores and spatial distances"
  - "pg_trgm + GiST index on name column for fuzzy matching in discovery pipeline"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-06-26
---

# Phase 4 Plan 1: CandidateModel Summary

**CandidateModel with four-state matching, confidence scoring, evidence JSONB, pg_trgm fuzzy name index, and Pydantic schemas**

## Performance

- **Duration:** 3 min
- **Started:** 2026-06-26T03:40:16Z
- **Completed:** 2026-06-26T03:43:38Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments
- CandidateModel with source_type/match_status/confidence CheckConstraints per DISC-03/DISC-06
- Geometry(Point 4326) with spatial GiST index, pg_trgm extension and trgm GiST index on name for fuzzy matching
- Pydantic schemas for full CRUD workflow: CandidateCreate, CandidateResponse, CandidateListResponse, CandidateReviewRequest, CandidateMatchResult
- 17 tests covering model creation, CheckConstraint definitions, and schema validation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CandidateModel, migration, schemas, and tests** - `6e9df53` (feat)

## Files Created/Modified
- `apps/api/src/api/models/candidate.py` - CandidateModel with CheckConstraints and indexes
- `apps/api/alembic/versions/0008_candidates.py` - Migration creating candidates table, pg_trgm extension, spatial and trgm indexes
- `apps/api/src/api/models/__init__.py` - Added CandidateModel to barrel exports
- `apps/api/src/api/schemas/candidates.py` - Pydantic schemas for CRUD, review, and match result
- `apps/api/tests/test_candidates.py` - 17 tests for model, constraints, and schemas

## Decisions Made
- ORM-level defaults (match_status="unmatched", confidence="MEDIUM") are SQL INSERT defaults — service layer must set them explicitly at ORM construction time, matching the project pattern (StructureModel.status uses same approach)
- Migration 0008 branches from 0006 (inspections merge migration) as the latest in the chain — no 0007 exists since no intermediate migration was created

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test expectations for ORM default values**
- **Found during:** Task 1 (test_candidates.py)
- **Issue:** Tests expected match_status, confidence, id, created_at, updated_at to auto-populate from column defaults during ORM constructor, but SQLAlchemy `default` only applies at SQL INSERT level, not Python object construction
- **Fix:** Adjusted tests to explicitly set match_status and confidence in constructor, and to provide id/timestamps when testing those fields. Verified column defaults are correctly defined for DB-level INSERT
- **Files modified:** apps/api/tests/test_candidates.py
- **Verification:** All 17 tests pass
- **Committed in:** 6e9df53 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor — test adjustment only, no functional change to the model or migration

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CandidateModel ready for discovery service (Plan 04-02) to create candidates from OSM
- Match result schema ready for matching engine output
- Review request schema ready for engineer review workflow
- pg_trgm extension and trgm index ready for fuzzy name matching in matching engine

---
*Phase: 04-discovery-matching-backend*
*Completed: 2026-06-26*

## Self-Check: PASSED

- All 4 created files found on disk
- Commit 6e9df53 found in git log
- All 17 tests pass (uv run pytest tests/test_candidates.py -x -q)
