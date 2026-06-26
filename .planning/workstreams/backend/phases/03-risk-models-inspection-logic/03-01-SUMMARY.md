---
phase: 03-risk-models-inspection-logic
plan: 01
subsystem: api
tags: [risk-engine, python, pytest, tdd, semi-quantitative, hydraulic-structures]

# Dependency graph
requires:
  - phase: 02-data-ingestion-spatial-api
    provides: StructureModel with wear_percentage, technical_condition, type fields that feed the risk computation
provides:
  - RiskAssessment dataclass with 10 fields for full explainability
  - compute_risk() pure Python entry point taking dict inputs
  - compute_condition_score() blended condition score with weight redistribution
  - detect_red_flags() red-flag detection with 6 trigger conditions
  - _seasonal_modifier() Kazakhstan flood-season urgency multiplier
  - _staleness_modifier() data freshness multiplier
  - _CONDITION_MAP, _CONSEQUENCE_BY_TYPE, _REDFLAG_KEYWORDS lookup tables
affects: [03-03-risk-assessment-persistence, 03-05-inspection-history, 03-06-export-endpoints, 05-rag-agent-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure Python computation module — no DB, no async, no side effects, fully unit-testable"
    - "TDD RED/GREEN cycle: 36 failing tests written first, then implementation to pass all"
    - "Semi-quantitative risk formula: condition * consequence * seasonal * staleness"
    - "Weight redistribution in blended score when data components are missing"
    - "Weak-evidence floor: never allow repair status below 'inspection_required' when evidence is weak"

key-files:
  created:
    - apps/api/src/api/services/risk_engine.py
    - apps/api/tests/test_risk_engine.py
  modified: []

key-decisions:
  - "Implemented exactly per RESEARCH.md Pattern 2 reference implementation and D-01 through D-09 decisions"
  - "Used dict inputs (not ORM models) for compute_risk() to maintain purity and testability"
  - "Red-flag keyword matching is case-insensitive substring search against Russian keywords"
  - "Weight redistribution proportional when condition/inspection data is missing"

patterns-established:
  - "Pure Python computation module pattern: isolate complex domain logic from DB/async for unit testability"
  - "TDD pattern for analytical modules: comprehensive test suite covering all decision branches before implementation"

requirements-completed: [RISK-01, RISK-02, RISK-03, RISK-04, RISK-05]

# Metrics
duration: 7min
completed: 2026-06-26
---

# Phase 03 Plan 01: Risk Engine TDD Summary

**Pure Python risk computation module with semi-quantitative formula (condition x consequence x seasonal x staleness), 6-band interval mapping, red-flag overrides, 4 repair statuses, and weak-evidence floor — 36 unit tests covering RISK-01 through RISK-05**

## Performance

- **Duration:** 7 min
- **Started:** 2026-06-26T00:48:10Z
- **Completed:** 2026-06-26T00:55:23Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Implemented risk engine as pure Python module with zero project imports (D-01) — fully unit-testable, no DB/async coupling
- Comprehensive TDD test suite with 36 test functions across 9 test classes covering all decision branches (D-02 through D-09)
- Semi-quantitative risk formula with explainable factor breakdown: condition_score, consequence_factor, seasonal_modifier, staleness_modifier, composite_score
- Red-flag detection with 6 trigger conditions: wear>=80%, аварийное condition, and 4 Russian keyword matches
- Weak-evidence floor prevents false certainty — never allows repair status below "inspection_required" when data is stale, low-confidence, or missing

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Write comprehensive failing tests** - `22b5bbf` (test)
2. **Task 2: GREEN — Implement risk_engine.py** - `c68fc7e` (feat)

_Note: TDD tasks have separate test and feat commits (RED/GREEN cycle)_

## Files Created/Modified
- `apps/api/src/api/services/risk_engine.py` - Pure Python risk computation module with RiskAssessment dataclass, compute_risk(), compute_condition_score(), detect_red_flags(), _seasonal_modifier(), _staleness_modifier()
- `apps/api/tests/test_risk_engine.py` - 36 unit tests across 9 test classes covering RISK-01 through RISK-05

## Decisions Made
- Followed RESEARCH.md Pattern 2 reference implementation exactly — no deviations from planned formula or thresholds
- Used dict inputs (matching StructureModel field names) rather than ORM model objects to maintain module purity
- Red-flag keyword matching uses case-insensitive substring search — simple and effective for Russian inspection findings text
- Weight redistribution in compute_condition_score is proportional (weights normalize to 1.0 over available components)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in `test_provenance.py::TestProvenanceFKEnforcement::test_fact_has_provenance` — integration test requires running Docker PostgreSQL stack (hostname `postgres:5432` doesn't resolve outside Docker). Unrelated to this plan's changes. Not fixed per scope boundary rules.

## TDD Gate Compliance

- RED gate: `test(03-01): add failing tests for risk engine` commit exists (22b5bbf) — all 36 tests failed with ModuleNotFoundError before implementation
- GREEN gate: `feat(03-01): implement risk engine computation module` commit exists (c68fc7e) — all 36 tests pass after implementation
- Gate sequence verified: RED commit precedes GREEN commit in git log

## Next Phase Readiness
- Risk engine module is ready for integration by 03-03 (Risk Assessment Persistence) which will call compute_risk() and persist results to risk_assessments table
- The dict-based interface means the persistence layer can convert ORM model instances to dicts before calling compute_risk()
- All exported symbols (RiskAssessment, compute_risk, compute_condition_score, detect_red_flags) are available for downstream plans
- Export endpoints (03-06) can use RiskAssessment fields for trilingual report generation

## Self-Check: PASSED

- FOUND: apps/api/src/api/services/risk_engine.py
- FOUND: apps/api/tests/test_risk_engine.py
- FOUND: .planning/workstreams/backend/phases/03-risk-models-inspection-logic/03-01-SUMMARY.md
- FOUND: 22b5bbf (test commit)
- FOUND: c68fc7e (feat commit)

---
*Phase: 03-risk-models-inspection-logic*
*Completed: 2026-06-26*
