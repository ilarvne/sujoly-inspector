---
phase: 03-risk-models-inspection-logic
plan: 04
subsystem: backend
tags: [documents, minio, crud, rbac, provenance]
dependency_graph:
  requires: [03-02]
  provides: [document-attachment-endpoints]
  affects: []
tech_stack:
  added: []
  patterns: [FastAPI APIRouter, SQLAlchemy async CRUD, MinIO presigned URLs, Pydantic Literal enums]
key_files:
  created:
    - apps/api/alembic/versions/0005_documents.py
    - apps/api/src/api/models/document.py
    - apps/api/src/api/services/document_service.py
    - apps/api/src/api/routes/documents.py
    - apps/api/src/api/schemas/documents.py
    - apps/api/tests/test_documents.py
  modified: []
decisions:
  - Branched migration 0005 from 0003 (not 0004) to allow parallel Wave 2 execution with Plan 03-03
  - Used module-level import pattern (from api.services import document_service) in routes instead of direct function imports — consistent with emerging pattern
  - Added presigned_download_url=None to mock document defaults to prevent Pydantic validation errors with MagicMock auto-attributes
metrics:
  duration: 4min
  tasks: 2
  files: 6
  completed: "2026-06-26"
---

# Phase 03 Plan 04: Document Attachment Endpoints with MinIO Summary

Document attachment CRUD endpoints with MinIO integration, RBAC enforcement, and provenance tracking — DATA-06 complete.

## One-liner

Document CRUD with MinIO presigned URLs, RBAC (inspector/admin), and provenance tracking per DATA-06/D-17/D-18

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | RED — Write failing tests for document endpoints | 5c0b8b6 | apps/api/tests/test_documents.py |
| 2 | GREEN — Implement documents migration, model, service, routes | 3cac4be | 6 files (migration, model, service, routes, schemas, tests) |

## Key Artifacts

| Symbol | Type | File | Purpose |
|--------|------|------|---------|
| `DocumentModel` | ORM model | `apps/api/src/api/models/document.py` | Documents table with type, language, MinIO keys per D-17 |
| `register_document()` | function | `apps/api/src/api/services/document_service.py` | Create document with provenance |
| `get_document()` | function | `apps/api/src/api/services/document_service.py` | Fetch document by ID |
| `list_documents()` | function | `apps/api/src/api/services/document_service.py` | List documents for a structure |
| `delete_document()` | function | `apps/api/src/api/services/document_service.py` | Delete DB record + MinIO object |
| `get_download_url()` | function | `apps/api/src/api/services/document_service.py` | Generate presigned download URL |
| `DocumentCreate` | schema | `apps/api/src/api/schemas/documents.py` | Request body with Literal enum fields |
| `DocumentResponse` | schema | `apps/api/src/api/schemas/documents.py` | Response with ConfigDict(from_attributes=True) |
| `DocumentListResponse` | schema | `apps/api/src/api/schemas/documents.py` | List envelope |
| `POST /api/v1/structures/{id}/documents` | endpoint | `apps/api/src/api/routes/documents.py` | Register document (inspector+) per D-18 |
| `GET /api/v1/structures/{id}/documents` | endpoint | `apps/api/src/api/routes/documents.py` | List documents (viewer+) per D-18 |
| `DELETE /api/v1/documents/{id}` | endpoint | `apps/api/src/api/routes/documents.py` | Delete document (admin only) per D-18 |
| `GET /api/v1/documents/{id}/download` | endpoint | `apps/api/src/api/routes/documents.py` | Presigned download URL (viewer+) per D-18 |
| Migration 0005 | migration | `apps/api/alembic/versions/0005_documents.py` | Documents table with CheckConstraints |

## Deviations from Plan

None — plan executed exactly as written.

## TDD Gate Compliance

- RED gate: `test(03-04)` commit exists (5c0b8b6) — 10 failing tests
- GREEN gate: `feat(03-04)` commit exists (3cac4be) — all 10 tests passing
- No REFACTOR gate needed (implementation is clean)

## Threat Model Mitigations

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-03-10 | Presigned URL short expiry (2hr) | Implemented via MinIOService.presigned_download_url |
| T-03-11 | DELETE requires admin role | require_role("admin") dependency enforced |
| T-03-12 | POST requires inspector+ role | require_role("inspector") dependency enforced |
| T-03-13 | Literal enum fields prevent mass assignment | DocumentCreate uses Literal types for document_type, language |

## Test Results

```
tests/test_documents.py: 10 passed
Full suite (excluding integration): 116 passed, 2 skipped
```

## Deferred Issues

None.

## Self-Check: PASSED

All 6 created files verified on disk. Both commit hashes (5c0b8b6, 3cac4be) confirmed in git log.
