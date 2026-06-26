---
phase: 03-risk-models-inspection-logic
plan: 05
subsystem: backend
tags: [inspections, photos, minio, celery, risk-trigger, rbac, provenance]
dependency_graph:
  requires: ["03-02", "03-03", "03-04"]
  provides: [inspection-crud, inspection-photos, risk-trigger-inspection]
  affects: [structures, risk-assessments]
tech_stack:
  added: [InspectionModel, InspectionPhotoModel, inspection_service]
  patterns: [tdd-red-green, async-session, celery-dispatch, presigned-url, rbac-require-role]
key_files:
  created:
    - apps/api/alembic/versions/0006_inspections.py
    - apps/api/src/api/models/inspection.py
    - apps/api/src/api/services/inspection_service.py
    - apps/api/src/api/routes/inspections.py
    - apps/api/src/api/schemas/inspections.py
    - apps/api/tests/test_inspections.py
  modified: []
decisions:
  - Migration 0006 is a merge migration joining 0004 (risk_assessments) and 0005 (documents) branches
  - Recomputation trigger uses try/except dispatch pattern matching structure_service.update_structure
  - Module-level import pattern for inspection_service in routes (from api.services import inspection_service)
  - Presigned URLs generated on-demand in route layer (not stored in DB) per T-03-14 mitigation
metrics:
  duration: 4min
  completed: "2026-06-26"
  tasks: 2
  files: 6
---

# Phase 03 Plan 05: Inspection History with Photos Summary

Inspection history CRUD with photo attachments via MinIO and risk recomputation trigger on inspection creation (D-14, D-15, D-16, D-05 trigger #1)

## What Was Built

- **InspectionModel + InspectionPhotoModel ORM models**: Inspections table with findings, condition, red_flags JSONB, and provenance FK. Inspection photos linked via inspection_id FK with MinIO object keys.
- **Migration 0006 (merge)**: Joins branches 0004 (risk_assessments) and 0005 (documents). Creates both inspections and inspection_photos tables with proper FK constraints and indexes.
- **inspection_service**: Create inspection with photo attachments + provenance creation (source_type='inspection') + risk recomputation trigger via Celery. Get/list inspections with photo loading.
- **Inspection API routes**: POST (inspector+, 201), GET list (viewer+, with presigned URLs), GET detail (viewer+, with presigned URLs). RBAC enforced via require_role dependency.
- **Pydantic schemas**: InspectionCreate with photos array, PhotoMetadata with Literal photo_type, InspectionResponse, PhotoResponse with presigned_download_url, InspectionListResponse.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Merge migration 0006 joins 0004+0005 | Both branches need to be applied before inspections table can reference structures and provenance |
| Recomputation uses try/except dispatch | Matches existing pattern in structure_service.update_structure — graceful degradation if Celery unavailable |
| Module-level service import | `from api.services import inspection_service` — matches document_service pattern, avoids circular imports |
| Presigned URLs generated in route layer | Not stored in DB — generated on-demand via MinIOService with 2hr expiry per T-03-14 |

## TDD Gate Compliance

- RED commit: `test(03-05): add failing tests for inspection endpoints` (3427ebf) — 9 failing tests
- GREEN commit: `feat(03-05): implement inspection history with photos and recomputation trigger` (aa0c49e) — all 9 pass
- No REFACTOR needed (clean implementation)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed recomputation test patch target**
- **Found during:** Task 2 GREEN phase
- **Issue:** Test patched `api.services.inspection_service.recompute_structure_risk` but the function uses a local import inside `create_inspection`
- **Fix:** Changed patch target to `api.tasks.celery_tasks.recompute_structure_risk` where the actual task lives
- **Files modified:** apps/api/tests/test_inspections.py
- **Commit:** aa0c49e

None other — plan executed exactly as written.

## Verification Results

All 9 inspection tests pass:
```
tests/test_inspections.py .........                                      [100%]
```
Full regression suite (excluding integration test requiring real DB): 112 passed, 0 failed.

## Threat Model Verification

| Threat ID | Mitigation | Status |
|-----------|------------|--------|
| T-03-14 | Photo presigned URLs with 2hr expiry, not logged | ✅ Implemented — `presigned_download_url` generated on-demand |
| T-03-15 | require_role("inspector") for POST | ✅ Implemented — test_create_inspection_viewer_forbidden asserts 403 |
| T-03-16 | Explicit InspectionCreate Pydantic schema with typed fields | ✅ Implemented — photo_type is Literal enum |
| T-03-17 | Photo object keys stored as-is, MinIO validates | ✅ Accepted per plan |

## Self-Check: PASSED

All created files exist. Both commits (RED 3427ebf, GREEN aa0c49e) found in git log.
