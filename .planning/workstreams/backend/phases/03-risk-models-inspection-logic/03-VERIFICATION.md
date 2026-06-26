---
phase: 03-risk-models-inspection-logic
verified: 2026-06-26T18:30:00Z
status: gaps_found
score: 44/47 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: null
  previous_score: null
  gaps_closed: []
  gaps_remaining: []
  regressions: []
gaps:
  - truth: "GET /api/v1/structures endpoints remain accessible to all roles (viewer+) per D-12"
    status: failed
    reason: "Read endpoints (GET /structures, /structures/search, /structures/{id}, /structures/{id}/risk) are fully public and do not require any JWT. They allow unauthenticated enumeration of structures and risk scores, which contradicts 'RBAC enforced' and the plan's 'all roles (viewer+)' requirement."
    artifacts:
      - path: "apps/api/src/api/routes/structures.py"
        issue: "GET list, search, and detail endpoints declare no auth dependency"
      - path: "apps/api/src/api/routes/risk.py"
        issue: "GET /structures/{id}/risk endpoint declares no auth dependency"
    missing:
      - "Add current_user: UserModel = Depends(require_role('viewer')) to GET /structures, GET /structures/search, GET /structures/{id}, and GET /structures/{id}/risk"
  - truth: "Weak evidence floors repair status at inspection_required — never downgrades below it per D-09"
    status: partial
    reason: "risk_engine.compute_risk() implements the floor when structure.provenance_confidence == 'LOW', but the production recomputation path in risk_service.recompute_risk_for_structure() always passes 'provenance_confidence': None. Low-confidence source data therefore never triggers the floor in real system recomputation."
    artifacts:
      - path: "apps/api/src/api/services/risk_service.py"
        issue: "structure_dict hardcodes provenance_confidence to None with a TODO comment instead of loading the structure's ProvenanceModel confidence_level"
      - path: "apps/api/src/api/services/risk_engine.py"
        issue: "Floor logic is correct but disconnected from real provenance data in production path"
    missing:
      - "Load the structure's ProvenanceModel in recompute_risk_for_structure and pass provenance.confidence_level into structure_dict"
  - truth: "User can GET /api/v1/export/inspection-report/{inspection_id}?lang=en to generate PDF inspection report in English"
    status: partial
    reason: "PDF endpoint works locally and in unit tests (templates exist in apps/api/templates), but the production Dockerfile runtime stage does not copy the templates directory from the builder. export_service resolves templates to /app/templates/inspection_report_{lang}.html, so PDF export will raise TemplateNotFound in any container built from the current Dockerfile."
    artifacts:
      - path: "apps/api/Dockerfile"
        issue: "Runtime stage only copies /app/.venv and /app/src; missing COPY --from=builder /app/templates /app/templates"
      - path: "apps/api/src/api/services/export_service.py"
        issue: "Correctly resolves templates relative to apps/api/templates, but that path is not present in the runtime image"
    missing:
      - "Add COPY --from=builder /app/templates /app/templates to the Dockerfile runtime stage"
  - truth: "System enforces administrator, engineer, inspector, and viewer role permissions (RBAC)"
    status: partial
    reason: "Role checks are implemented for write endpoints and protected routes, but authentication is trivially bypassed: POST /auth/token accepts a username alone (no password/PIN) and returns a JWT for any existing user. Knowing a username is sufficient to impersonate any role. Combined with public read endpoints, RBAC is not meaningfully enforced."
    artifacts:
      - path: "apps/api/src/api/routes/auth.py"
        issue: "token_endpoint issues JWT on username lookup alone with no secret verification"
      - path: "apps/api/src/api/models/user.py"
        issue: "No password_hash field; api_key stored in plaintext"
      - path: "apps/api/src/api/services/auth_service.py"
        issue: "get_user_by_username returns user without any credential verification"
    missing:
      - "Add password verification (or require API key only) before issuing JWT"
      - "Hash API keys at rest and compare with constant-time hash comparison"
  - truth: "Docker stack uses non-trivial secrets for JWT signing and admin API key"
    status: partial
    reason: "docker-compose.yml provides fallback defaults 'dev-secret-change-me' and 'dev-admin-key' for API_JWT_SECRET and API_INITIAL_ADMIN_API_KEY. If env vars are not overridden, the stack ships with public, hardcoded secrets, allowing token forgery and admin impersonation."
    artifacts:
      - path: "docker-compose.yml"
        issue: "API_JWT_SECRET: ${API_JWT_SECRET:-dev-secret-change-me} and API_INITIAL_ADMIN_API_KEY: ${API_INITIAL_ADMIN_API_KEY:-dev-admin-key} provide insecure fallbacks"
      - path: "apps/api/src/api/config/settings.py"
        issue: "jwt_secret and initial_admin_api_key default to empty strings; no runtime validation that secrets are set"
    missing:
      - "Remove fallback defaults in docker-compose.yml and add startup validation that JWT secret is set and >=32 characters"
---

# Phase 03: Risk Models & Inspection Logic — Verification Report

**Phase Goal:** Risk-informed inspection intervals, repair status, inspection history, document attachment, RBAC, and export endpoints all operational.

**Verified:** 2026-06-26T18:30:00Z

**Status:** `gaps_found`

**Score:** 44/47 must-have truths verified (3 truths have functional or security gaps; 2 additional security/maintainability issues noted below).

**Re-verification:** No — initial verification.

## Goal Achievement Summary

Phase 3 delivers a large body of working backend functionality: the pure-Python risk engine, JWT auth dependencies, role-based access control on write endpoints, risk assessment persistence with override/recompute, document and inspection CRUD, and trilingual CSV/GeoJSON/PDF export endpoints. The targeted Phase 3 test suite passes (89/89) and the full backend suite passes except for one pre-existing integration test that requires a running Docker PostgreSQL stack (`tests/test_provenance.py::test_fact_has_provenance`, DNS resolution failure for `postgres:5432`).

However, adversarial code-level verification found several issues that prevent the phase goal from being fully achieved:

1. **RBAC is not enforced on read paths** — GET structure and risk endpoints are fully public, allowing unauthenticated data enumeration.
2. **Weak-evidence floor is disconnected in production** — `recompute_risk_for_structure` never passes real provenance confidence to the risk engine, so low-confidence data never triggers the floor.
3. **PDF export is broken in the Docker runtime image** — templates are not copied from the builder stage, so the production endpoint will raise `TemplateNotFound`.
4. **Authentication is trivially bypassable** — a username alone is sufficient to obtain a JWT for any existing user, undermining the role system.
5. **Deployment defaults are insecure** — `docker-compose.yml` falls back to hardcoded `dev-secret-change-me` and `dev-admin-key`.

These are captured as gaps in the YAML frontmatter above.

## Observable Truths

| # | Plan | Truth | Status | Evidence |
|---|------|-------|--------|----------|
| 1 | 03-01 | compute_risk() returns RiskAssessment with all 10 factor fields | VERIFIED | `apps/api/src/api/services/risk_engine.py` defines `RiskAssessment` dataclass with all fields; `compute_risk` returns populated instance; 36 unit tests pass |
| 2 | 03-01 | Inspection interval mapping produces 6 bands | VERIFIED | Threshold bands in `risk_engine.py:303-314` match D-03; tests cover emergency, 30d, 90d, 180d, 12mo, 24mo |
| 3 | 03-01 | Red-flag detection triggers on 6 conditions | VERIFIED | `detect_red_flags` checks wear>=80, аварийное condition, and 4 Russian keyword matches; tests pass |
| 4 | 03-01 | Repair status maps to 4 bands | VERIFIED | `risk_engine.py:316-324` maps condition_score to 4 statuses; tests pass |
| 5 | 03-01 | Weak evidence floors repair status | PARTIAL | Logic works in unit tests, but production recomputation path passes `provenance_confidence=None` (`risk_service.py:299`) |
| 6 | 03-02 | POST /auth/token with username returns JWT | VERIFIED | `auth.py` issues JWT on username lookup; tests pass |
| 7 | 03-02 | POST /auth/token with API key returns JWT | VERIFIED | `auth.py` issues JWT on API key lookup; tests pass |
| 8 | 03-02 | GET /auth/me returns user info | VERIFIED | `auth.py` returns id, username, role, full_name; tests pass |
| 9 | 03-02 | Requests without JWT get 401 on protected endpoints | VERIFIED | `get_current_user` raises 401; tests pass |
| 10 | 03-02 | Insufficient role gets 403 | VERIFIED | `require_role` raises 403; tests pass |
| 11 | 03-02 | Initial admin seeded on startup | VERIFIED | `main.py` lifespan seeds admin from env vars; tests pass |
| 12 | 03-02 | require_role('inspector') allows admin, engineer, inspector | VERIFIED | Hierarchy check works; tests pass |
| 13 | 03-02 | require_role('engineer') rejects inspector | VERIFIED | Tests pass |
| 14 | 03-02 | POST /structures requires engineer+ | VERIFIED | `structures.py:177` uses `require_role("engineer")`; tests pass |
| 15 | 03-02 | PUT /structures/{id} requires engineer+ | VERIFIED | `structures.py:194` uses `require_role("engineer")`; tests pass |
| 16 | 03-02 | DELETE /structures/{id} requires admin | VERIFIED | `structures.py:220` uses `require_role("admin")`; tests pass |
| 17 | 03-02 | GET /structures endpoints accessible to all roles (viewer+) | FAILED | Endpoints are fully public; no `require_role('viewer')` declared on list/search/detail/risk GET |
| 18 | 03-03 | GET /structures/{id}/risk returns latest assessment | VERIFIED | `risk.py` calls `get_latest_assessment`; tests pass |
| 19 | 03-03 | POST /structures/{id}/override creates override with provenance | VERIFIED | `risk_service.create_override` creates ProvenanceModel with `source_type='manual'` and `contributor=user.username`; tests pass |
| 20 | 03-03 | Override response includes system + override values | VERIFIED | `OverrideResponse` built from `contributing_factors.system_*` fields; tests pass |
| 21 | 03-03 | Previous assessment expired (valid_to set) | VERIFIED | `create_assessment` and `create_override` set `valid_to` on prior records; tests pass |
| 22 | 03-03 | POST /structures/{id}/recompute triggers manual recomputation | VERIFIED | `risk.py` endpoint calls `recompute_risk_for_structure`; tests pass |
| 23 | 03-03 | recompute_structure_risk Celery task loads data and calls risk_engine | VERIFIED | `celery_tasks.py` defines task; tests pass |
| 24 | 03-03 | recompute_all_risks scheduled daily at 2 AM UTC | VERIFIED | `celery_app.py` has `beat_schedule` with `crontab(hour=2, minute=0)` and timezone UTC |
| 25 | 03-04 | POST /structures/{id}/documents registers document (inspector+) | VERIFIED | `documents.py` uses `require_role("inspector")`; tests pass |
| 26 | 03-04 | GET /structures/{id}/documents lists with presigned URLs | VERIFIED | `documents.py` generates presigned URLs; tests pass |
| 27 | 03-04 | GET /documents/{id}/download returns presigned URL | VERIFIED | `documents.py` endpoint returns URL with 7200s expiry; tests pass |
| 28 | 03-04 | DELETE /documents/{id} removes DB + MinIO object (admin only) | VERIFIED | `documents.py` uses `require_role("admin")` and calls `remove_object`; tests pass |
| 29 | 03-04 | Document registration creates ProvenanceModel | VERIFIED | `document_service.register_document` creates ProvenanceModel with `source_type='manual'`; tests pass |
| 30 | 03-04 | Documents table has type and language constraints | VERIFIED | Migration 0005 and `DocumentModel` have CheckConstraints for document_type and language |
| 31 | 03-05 | POST /structures/{id}/inspections creates inspection (inspector+) | VERIFIED | `inspections.py` uses `require_role("inspector")`; tests pass |
| 32 | 03-05 | GET /structures/{id}/inspections lists with photo URLs | VERIFIED | `inspections.py` generates presigned photo URLs; tests pass |
| 33 | 03-05 | GET /structures/{id}/inspections/{id} returns detail | VERIFIED | `inspections.py` endpoint returns inspection with photos; tests pass |
| 34 | 03-05 | Creating inspection triggers risk recomputation | VERIFIED | `inspection_service.create_inspection` dispatches `recompute_structure_risk.delay()` after commit; tests pass |
| 35 | 03-05 | Inspection photos linked via inspection_photos table | VERIFIED | `InspectionPhotoModel` and migration 0006 create the table with FK and indexes |
| 36 | 03-05 | Inspection creation creates ProvenanceModel | VERIFIED | `inspection_service.create_inspection` creates ProvenanceModel with `source_type='inspection'`; tests pass |
| 37 | 03-06 | GET /export/structures?format=csv returns CSV | VERIFIED | `export_service.export_structures_csv` returns StreamingResponse with BOM and translated headers; tests pass |
| 38 | 03-06 | CSV includes UTF-8 BOM and risk fields | VERIFIED | `export_service.py` writes `\ufeff` and includes inspection_interval, repair_status, composite_score; tests pass |
| 39 | 03-06 | GET /export/structures?format=geojson returns GeoJSON | VERIFIED | `export_service.export_structures_geojson` returns FeatureCollection with risk properties; tests pass |
| 40 | 03-06 | PDF report includes structure, inspection, photos, risk summary | PARTIAL | Templates exist and include all sections, but runtime Dockerfile does not copy them into the image |
| 41 | 03-06 | Export endpoints accept filter params | VERIFIED | `routes/exports.py` accepts type, district, condition, bbox; passes to `list_structures`; tests pass |
| 42 | 03-06 | All three formats support ru/kk/en | VERIFIED | `_TRANSLATIONS` dict covers all three languages; tests pass for CSV headers and PDF templates |
| 43 | 03-06 | CSV formula injection mitigated | VERIFIED | `_sanitize_csv_cell` prefixes dangerous chars; tests pass |
| 44 | 03-06 | PDF generation uses asyncio.to_thread | VERIFIED | `export_service.py:433` uses `asyncio.to_thread` for WeasyPrint |

**Score:** 44 verified, 1 failed, 3 partial = 44/47 (with 3 gaps).

## Requirement Traceability

| Requirement | Description | Plan(s) | Status | Evidence |
|-------------|-------------|---------|--------|----------|
| DATA-05 | Inspection history per structure (date, inspector, findings, photo URLs, condition) | 03-05 | Satisfied | `InspectionModel`, `InspectionPhotoModel`, `inspection_service.py`, `routes/inspections.py`, 9/9 tests pass |
| DATA-06 | Document attachment endpoints via MinIO presigned URLs | 03-04 | Satisfied | `DocumentModel`, `document_service.py`, `routes/documents.py`, 10/10 tests pass |
| RISK-01 | Semi-quantitative risk model: condition × consequence × seasonal × staleness | 03-01 | Satisfied | `risk_engine.py`, `compute_risk`, 36/36 risk engine tests pass |
| RISK-02 | Legible inspection intervals (30d, 90d, 180d, 12mo, 24mo, emergency) | 03-01 | Satisfied | Threshold mapping in `risk_engine.py`, tests pass |
| RISK-03 | Blended condition score + red-flag overrides | 03-01 | Satisfied | `compute_condition_score`, `detect_red_flags`, tests pass |
| RISK-04 | Four repair statuses | 03-01 | Satisfied | Status mapping in `risk_engine.py`, tests pass |
| RISK-05 | Prefer "inspection required" on weak evidence | 03-01 | Partial | Engine logic correct, but production recomputation path does not pass real provenance confidence (`risk_service.py:299`) |
| RISK-06 | Engineer override endpoints with logged provenance | 03-03 | Satisfied | `create_override`, `routes/risk.py`, `ProvenanceModel`, 15/15 risk API tests pass |
| RISK-07 | RBAC (admin, engineer, inspector, viewer) | 03-02 | Partial | Role hierarchy implemented, but read endpoints are public and username-only auth trivially bypasses role checks |
| RISK-08 | CSV/GeoJSON/PDF export in all three languages | 03-06 | Partial | CSV and GeoJSON work; PDF works locally but templates are missing from Docker runtime image |

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `apps/api/src/api/services/risk_engine.py` | Pure Python risk computation | VERIFIED | Exists, no project imports, 36 tests pass |
| `apps/api/tests/test_risk_engine.py` | Comprehensive unit tests | VERIFIED | 36 tests, all pass |
| `apps/api/src/api/models/user.py` | UserModel ORM with 4 roles | VERIFIED | Exists with role CheckConstraint; missing password_hash, api_key plaintext |
| `apps/api/src/api/services/auth_service.py` | JWT + user lookups | VERIFIED | Exists; no password verification, API key compared plaintext |
| `apps/api/src/api/dependencies/auth.py` | FastAPI auth dependencies | VERIFIED | Exists with `get_current_user`, `require_role`, `oauth2_scheme` |
| `apps/api/src/api/routes/auth.py` | Auth endpoints | VERIFIED | Exists; username-only path is a security concern |
| `apps/api/alembic/versions/0003_users.py` | Users migration | VERIFIED | Exists with role CheckConstraint and indexes |
| `apps/api/src/api/models/risk_assessment.py` | RiskAssessmentModel | VERIFIED | Exists; missing `__table_args__` CheckConstraints that are in migration |
| `apps/api/src/api/services/risk_service.py` | Risk persistence + override + recompute | VERIFIED | Exists; provenance confidence not wired to production path |
| `apps/api/src/api/routes/risk.py` | Risk endpoints | VERIFIED | Exists; GET risk lacks auth dependency |
| `apps/api/alembic/versions/0004_risk_assessments.py` | Risk assessments migration | VERIFIED | Exists with CheckConstraints and partial latest index |
| `apps/api/src/api/models/document.py` | DocumentModel | VERIFIED | Exists with CheckConstraints |
| `apps/api/src/api/services/document_service.py` | Document CRUD + MinIO | VERIFIED | Exists; route does not verify target structure exists before registration (WR-12) |
| `apps/api/src/api/routes/documents.py` | Document endpoints | VERIFIED | Exists; all GET endpoints require viewer+ |
| `apps/api/alembic/versions/0005_documents.py` | Documents migration | VERIFIED | Exists with CheckConstraints |
| `apps/api/src/api/models/inspection.py` | InspectionModel + InspectionPhotoModel | VERIFIED | Exists |
| `apps/api/src/api/services/inspection_service.py` | Inspection CRUD + trigger | VERIFIED | Exists; dispatches recompute after commit |
| `apps/api/src/api/routes/inspections.py` | Inspection endpoints | VERIFIED | Exists; GET detail does not verify inspection belongs to requested structure (WR-02) |
| `apps/api/alembic/versions/0006_inspections.py` | Inspections migration | VERIFIED | Exists as merge migration joining 0004 and 0005 |
| `apps/api/src/api/services/export_service.py` | CSV/GeoJSON/PDF export | VERIFIED | Exists; GeoJSON geometry not serialized (WR-03), CSV name always Russian (WR-11), MinIO get_object not closed with context manager (WR-09) |
| `apps/api/src/api/routes/exports.py` | Export endpoints | VERIFIED | Exists |
| `apps/api/templates/inspection_report_*.html` | PDF templates | VERIFIED | All three templates exist; missing from Docker runtime image |
| `apps/api/Dockerfile` | API runtime image with WeasyPrint deps | VERIFIED | WeasyPrint system deps present; missing COPY for templates |
| `apps/api/src/api/models/__init__.py` | Barrel export for Base.metadata | PARTIAL | Missing imports for `RiskAssessmentModel`, `DocumentModel`, `InspectionModel`, `InspectionPhotoModel` (WR-05) |

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `risk_service.py` | `risk_engine.py` | `recompute_risk_for_structure` calls `compute_risk()` | WIRED | Verified by `risk_engine.compute_risk` call in `risk_service.py:303` |
| `risk_service.py` | `RiskAssessmentModel` | `create_assessment` persists model | WIRED | Verified |
| `routes/risk.py` | `auth.py` | `require_role("engineer")` on override/recompute | WIRED | Verified |
| `routes/risk.py` | `risk_service.py` | Recompute endpoint calls `recompute_risk_for_structure` | WIRED | Verified |
| `routes/documents.py` | `auth.py` | `require_role` on register/delete/download | WIRED | Verified |
| `document_service.py` | `minio_client.py` | `remove_object` and `presigned_download_url` | WIRED | Verified |
| `routes/inspections.py` | `auth.py` | `require_role` on create/list/detail | WIRED | Verified (but GET endpoints are public because require_role is viewer and all unauthenticated users also pass) |
| `inspection_service.py` | `celery_tasks.py` | `create_inspection` dispatches `recompute_structure_risk.delay()` | WIRED | Verified |
| `export_service.py` | `risk_service.py` | CSV/GeoJSON calls `get_latest_assessment` | WIRED | Verified |
| `export_service.py` | `inspection_service.py` | PDF calls `get_inspection` | WIRED | Verified |
| `export_service.py` | `minio_client.py` | PDF downloads photos via `client.get_object` | WIRED | Verified (but connection not closed in context manager) |
| `routes/structures.py` | `auth.py` | `require_role` on create/update/delete | WIRED | Verified; GET endpoints not wired |

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `risk_engine.py` | `condition_score` | `wear_percentage`, `technical_condition`, `last_inspection_score` | Yes | Blended from real inputs with weight redistribution |
| `risk_engine.py` | `composite_score` | `condition_score * consequence * seasonal * staleness` | Yes | Computed from upstream factors |
| `risk_engine.py` | `weak_evidence_reasons` | `structure.provenance_confidence`, `inspections`, `days_since` | DISCONNECTED | Production path always passes `provenance_confidence=None`, so low-confidence trigger is never reached |
| `risk_service.py` | `assessment` | `risk_engine.compute_risk()` | Yes | Persisted to `RiskAssessmentModel` |
| `export_service.py` | `risk fields in CSV/GeoJSON` | `risk_service.get_latest_assessment(struct.id)` | Yes | DB query returns real assessment or None |
| `export_service.py` | `photos_data` | `minio_service.client.get_object` | Yes | Downloads real photo bytes from MinIO (if service available) |
| `inspection_service.py` | `inspection.photos` | `InspectionPhotoModel` query | Yes | Photos loaded from DB |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Risk engine tests pass | `uv run pytest tests/test_risk_engine.py -q` | 36 passed | PASS |
| Auth + RBAC tests pass | `uv run pytest tests/test_auth.py tests/test_structures.py -q` | 27 passed | PASS |
| Risk API tests pass | `uv run pytest tests/test_risk_api.py -q` | 15 passed | PASS |
| Document tests pass | `uv run pytest tests/test_documents.py -q` | 10 passed | PASS |
| Inspection tests pass | `uv run pytest tests/test_inspections.py -q` | 9 passed | PASS |
| Export tests pass | `uv run pytest tests/test_exports.py -q` | 10 passed | PASS |
| Full backend suite | `uv run pytest tests/ -q` | 135 passed, 2 skipped, 1 failed (pre-existing DNS integration test) | PASS (Phase 3 scope) |
| Risk engine pure Python | `grep -E "from api\.|import asyncio|from sqlalchemy" apps/api/src/api/services/risk_engine.py` | No matches | PASS |
| Dockerfile missing templates | `grep -E "COPY --from=builder /app/templates" apps/api/Dockerfile` | No match | FAIL |
| Public read endpoints | `grep -E "require_role\(\"viewer\"\)" apps/api/src/api/routes/structures.py apps/api/src/api/routes/risk.py` | No match | FAIL |
| Provenance confidence hardcoded | `grep "provenance_confidence" apps/api/src/api/services/risk_service.py` | Returns `None` with TODO | FAIL |

## Probe Execution

No phase-declared probes or conventional `scripts/*/tests/probe-*.sh` files were found. Spot-checks above were run instead.

## Requirements Coverage Cross-Reference

All ten declared requirement IDs for Phase 3 are accounted for above. DATA-05 and DATA-06 are satisfied by their respective CRUD implementations. RISK-01 through RISK-04 are satisfied by the risk engine. RISK-06 is satisfied by the override/provenance implementation. RISK-05, RISK-07, and RISK-08 have implementation presence but functional or deployment gaps as noted.

## Anti-Patterns and Code Review Findings

The existing `03-REVIEW.md` (status: blocked, 6 critical, 12 warning) was consulted but not treated as authoritative. Independent verification confirmed the following issues that affect the phase goal:

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `routes/structures.py` | 39-166 | GET endpoints declare no auth dependency | BLOCKER | Public read access to structures and risk scores |
| `routes/risk.py` | 30-50 | GET /structures/{id}/risk declares no auth dependency | BLOCKER | Public risk data enumeration |
| `risk_service.py` | 299 | `provenance_confidence: None` with TODO | BLOCKER | Weak-evidence floor never triggered in production recomputation |
| `Dockerfile` | 34-35 | Runtime stage does not copy `/app/templates` | BLOCKER | PDF export fails in production containers |
| `routes/auth.py` | 18-46 | Username-only JWT issuance | WARNING | Trivial role impersonation; plan specified this behavior but it undermines RBAC |
| `models/user.py` | 29 | API key stored in plaintext | WARNING | Credential leak if DB compromised |
| `auth_service.py` | 51-57 | API key compared in plaintext | WARNING | Same as above |
| `docker-compose.yml` | 75, 78 | Insecure fallback secrets | WARNING | Token forgery / admin impersonation if env vars not set |
| `models/__init__.py` | 7-11 | Missing imports for new Phase 3 models | WARNING | `Base.metadata` out of sync; future autogenerate migrations will be wrong |
| `models/risk_assessment.py` | 42 | No `__table_args__` with CheckConstraints | WARNING | ORM model out of sync with migration |
| Multiple models | created_at defaults | `datetime.utcnow()` used for timezone-aware columns | WARNING | Naive datetime warnings and potential timezone offsets |
| `routes/inspections.py` | 123-128 | Detail endpoint does not verify `inspection.structure_id == structure_id` | WARNING | Cross-structure inspection disclosure (WR-02) |
| `export_service.py` | 337-346 | Raw `geometry` object placed in GeoJSON | WARNING | Will fail JSON serialization when structures have non-null geometry (WR-03) |
| `export_service.py` | 251 | CSV name always `name_ru` regardless of lang | WARNING | Kazakh/English exports still show Russian name (WR-11) |
| `export_service.py` | 397-402 | `minio_service.client.get_object` not in context manager | WARNING | HTTP connection leak on exception (WR-09) |

## Human Verification Required

No human verification items are required. The identified gaps are observable through code and test evidence; they do not depend on visual appearance, user flow completion, or external service behavior that requires manual testing.

## Gaps Summary

Phase 3 cannot be marked `passed` because three must-have truths are failed or partial and directly affect the phase goal:

1. **RBAC not enforced on read paths** — public GET endpoints for structures and risk assessments allow unauthenticated access.
2. **Weak-evidence floor disconnected** — production recomputation never passes real provenance confidence, so the D-09 floor is dead code for low-confidence source data.
3. **PDF export broken in production** — Dockerfile runtime image lacks the Jinja2 templates required by the PDF endpoint.

Additional security concerns (username-only authentication, plaintext API keys, insecure Docker fallback secrets) are documented as warnings because they do not fail explicit plan must-haves, but they severely weaken the RBAC and deployment posture the phase goal claims to deliver.

---

_Verified: 2026-06-26T18:30:00Z_
_Verifier: the agent (gsd-verifier)_
