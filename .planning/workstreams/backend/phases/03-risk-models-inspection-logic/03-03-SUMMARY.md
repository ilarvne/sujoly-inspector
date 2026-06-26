---
phase: 03-risk-models-inspection-logic
plan: 03
subsystem: backend
tags: [risk, override, provenance, celery, recompute, d-04, d-05, d-13, risk-06]
dependency_graph:
  requires: [03-01, 03-02]
  provides: [risk_assessment_persistence, risk_override_endpoint, risk_recompute_endpoint, celery_risk_tasks]
  affects: [structure_service]
tech_stack:
  added: [celery-beat-schedule, crontab]
  patterns: [provenance-per-fact-override, late-import-guard, asyncio-run-in-celery]
key_files:
  created:
    - apps/api/alembic/versions/0004_risk_assessments.py
    - apps/api/src/api/models/risk_assessment.py
    - apps/api/src/api/services/risk_service.py
    - apps/api/src/api/routes/risk.py
    - apps/api/src/api/schemas/risk.py
  modified:
    - apps/api/src/api/tasks/celery_tasks.py
    - apps/api/src/api/celery_app.py
    - apps/api/src/api/services/structure_service.py
decisions:
  - OverrideResponse built from base RiskAssessmentResponse.model_dump() then OverrideResponse(**data) to avoid Pydantic from_attributes issues with MagicMock system fields
  - Late import guard for InspectionModel (Wave 3 dependency) ensures system functional at wave boundary
  - D-05 trigger 2 implemented as try/except dispatch in structure_service.update_structure
metrics:
  duration: 4min
  completed: 2026-06-26
  tasks: 2
  files: 8
---

# Phase 03 Plan 03: Risk Assessment Persistence + Override + Recompute Summary

Risk assessment persistence (D-04), engineer override with provenance audit trail (D-13, RISK-06), manual recompute endpoint (D-05 trigger 4), and Celery-based scheduled recomputation (D-05 trigger 3). Connects the pure Python risk engine to the database and API.

## One-liner

Risk assessments persisted with history tracking, engineer override with provenance audit trail, manual + scheduled recomputation via Celery Beat

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | RED — Write failing tests for risk API + override + recompute | 73420ac | apps/api/tests/test_risk_api.py |
| 2 | GREEN — Implement risk_assessments migration, model, service, routes, Celery tasks | 8e1f9a6 | 8 files (5 new, 3 modified) |

## Key Artifacts

| Symbol | Type | File | Purpose |
|--------|------|------|---------|
| `RiskAssessmentModel` | ORM model | `apps/api/src/api/models/risk_assessment.py` | Risk assessment persistence with history (valid_to) per D-04 |
| `get_latest_assessment()` | function | `apps/api/src/api/services/risk_service.py` | Fetch current risk assessment (valid_to IS NULL) |
| `create_assessment()` | function | `apps/api/src/api/services/risk_service.py` | Persist new assessment, expire previous |
| `create_override()` | function | `apps/api/src/api/services/risk_service.py` | Engineer override with provenance per D-13 |
| `recompute_risk_for_structure()` | function | `apps/api/src/api/services/risk_service.py` | Load data → call risk_engine → persist |
| `recompute_structure_risk` | Celery task | `apps/api/src/api/tasks/celery_tasks.py` | Event-driven risk recomputation per D-05 |
| `recompute_all_risks` | Celery task | `apps/api/src/api/tasks/celery_tasks.py` | Daily bulk recomputation per D-05 trigger 3 |
| `celery_app.conf.beat_schedule` | config | `apps/api/src/api/celery_app.py` | Daily 2 AM UTC schedule |
| `RiskAssessmentResponse` | schema | `apps/api/src/api/schemas/risk.py` | Full factor breakdown response |
| `OverrideRequest` | schema | `apps/api/src/api/schemas/risk.py` | Override request with Literal enum fields (T-03-07 mitigation) |
| `OverrideResponse` | schema | `apps/api/src/api/schemas/risk.py` | Response with system + override values |
| `GET /api/v1/structures/{id}/risk` | endpoint | `apps/api/src/api/routes/risk.py` | Retrieve latest risk assessment |
| `POST /api/v1/structures/{id}/override` | endpoint | `apps/api/src/api/routes/risk.py` | Engineer override with provenance per RISK-06 |
| `POST /api/v1/structures/{id}/recompute` | endpoint | `apps/api/src/api/routes/risk.py` | Manual risk recomputation per D-05 trigger 4 |

## D-05 Trigger Coverage

| Trigger | Description | Status |
|---------|-------------|--------|
| 1 | After new inspection | Deferred to Plan 03-05 (Wave 3) |
| 2 | After structure update | Implemented — dispatch in `structure_service.update_structure` |
| 3 | Celery Beat daily | Implemented — `recompute_all_risks` at 2 AM UTC |
| 4 | Manual API trigger | Implemented — `POST /structures/{id}/recompute` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] OverrideResponse validation error with mock attributes**
- **Found during:** Task 2 — running tests
- **Issue:** `OverrideResponse.model_validate(result)` tried to read `system_inspection_interval` and `system_repair_status` from the MagicMock result object, causing Pydantic validation errors (MagicMock is not a string)
- **Fix:** Changed route to build OverrideResponse from `RiskAssessmentResponse.model_validate(result).model_dump()` plus system values extracted from `contributing_factors`, then `OverrideResponse(**base_data)` instead of mutating after validate
- **Files modified:** `apps/api/src/api/routes/risk.py`
- **Commit:** 8e1f9a6

**2. [Rule 2 - Missing Critical] D-05 trigger 2 dispatch after structure update**
- **Found during:** Task 2 — plan noted this as "deferred to execution time"
- **Issue:** Plan specified adding `recompute_structure_risk.delay(str(structure.id))` after commit in `structure_service.update_structure` — this was missing
- **Fix:** Added try/except guarded dispatch of `recompute_structure_risk.delay()` in `structure_service.update_structure` after flush+refresh
- **Files modified:** `apps/api/src/api/services/structure_service.py`
- **Commit:** 8e1f9a6

## Threat Flags

No new threat surface beyond what was already in the plan's threat_model. All mitigations implemented:
- T-03-06 (IDOR): UUID PKs + require_role("engineer") + structure existence check
- T-03-07 (mass assignment): OverrideRequest with Literal enum fields only
- T-03-08 (repudiation): ProvenanceModel created with source_type="manual", contributor=user.username

## Known Stubs

| File | Stub | Reason |
|------|------|--------|
| `risk_service.py` | InspectionModel late import guard returns None | Wave 3 dependency — full accuracy requires Plan 03-05 |
| `risk_service.py` | `provenance_confidence: None` in structure_dict | TODO: derive from provenance record |

## Test Results

- 15/15 risk API tests pass
- 90/90 total tests pass (excluding pre-existing DB-requiring test_provenance FK test)
- No regressions

## Self-Check: PASSED

All 8 created/modified files exist on disk. Both commit hashes (73420ac, 8e1f9a6) found in git log.
