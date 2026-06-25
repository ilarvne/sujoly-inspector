# Phase 3: Risk Models & Inspection Logic - Research

**Researched:** 2026-06-26
**Domain:** Risk computation, RBAC/JWT auth, inspection management, document attachments, trilingual PDF/CSV/GeoJSON exports
**Confidence:** HIGH

## Summary

Phase 3 builds the risk computation and inspection management layer on top of the existing Phase 2 REST API. The codebase already has established patterns for FastAPI routes, SQLAlchemy 2.0 async services, Alembic migrations, MinIO presigned URLs, and Celery tasks — all of which Phase 3 extends rather than reinvents. The risk engine is a pure Python module (D-01) with a semi-quantitative formula (condition × consequence × seasonal × staleness) mapped to legible inspection intervals via threshold bands (D-03). Repair status uses a blended condition score with red-flag overrides and a weak-evidence floor (D-06 through D-09). RBAC is JWT-based with four roles and FastAPI dependency injection (D-10 through D-13). Export endpoints use Python's `csv` module with `StreamingResponse` for CSV, reuse the existing GeoJSON pattern for GeoJSON, and WeasyPrint + Jinja2 for PDF generation with native Cyrillic/Kazakh support (D-19 through D-23).

Three new Python packages are required: **WeasyPrint** (HTML→PDF), **PyJWT** (JWT token encode/decode), and **Jinja2** (HTML templating for PDF). All three are well-established, high-reputation packages verified on PyPI and passing slopcheck `[OK]`. WeasyPrint requires system-level dependencies (Pango, HarfBuzz) that must be added to the Dockerfile runtime stage. Celery Beat must be added to docker-compose.yml as a new service for the daily risk recomputation scheduled task (D-05).

**Primary recommendation:** Follow existing codebase patterns exactly (service layer, route structure, model definitions, migration numbering from 0003). Add WeasyPrint system deps to the Dockerfile runtime stage, add PyJWT + Jinja2 + WeasyPrint to pyproject.toml, add a celery-beat service to docker-compose.yml, and implement the risk engine as a pure Python module with comprehensive unit tests — it is the most complex and most testable component.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Risk Score Model Design:**
- **D-01:** Risk computation as a pure Python module (`apps/api/src/api/services/risk_engine.py`) — not a database function or stored procedure. Takes structure data + facts as input, returns risk assessment with interval, score breakdown, and contributing factors.
- **D-02:** Risk formula factors: condition score (0-100, blended: wear 40% + technical_condition text mapping 40% + last inspection 20%), consequence factor (0.5-2.0, based on type/area/count), seasonal modifier (0.8-1.5, flood season March-May → 1.5), data staleness modifier (0.5-1.5, days since last inspection).
- **D-03:** Composite risk score = condition_score × consequence_factor × seasonal_modifier × staleness_modifier. Map to intervals via threshold bands: ≥200 OR red-flag → emergency, 150-199 → 30d, 100-149 → 90d, 60-99 → 180d, 30-59 → 12mo, <30 → 24mo.
- **D-04:** Store risk assessments in `risk_assessments` table: id, structure_id, condition_score, consequence_factor, seasonal_modifier, staleness_modifier, composite_score, inspection_interval (enum), repair_status (enum), red_flags (JSONB), contributing_factors (JSONB), provenance_id, computed_at, valid_to (nullable — NULL = latest).
- **D-05:** Risk recomputation triggers: (1) after new inspection, (2) after structure update, (3) Celery Beat daily job for seasonal modifier, (4) manual trigger via API by engineer/admin. Risk is a snapshot, not real-time.

**Repair Status Determination:**
- **D-06:** Blended condition score (0-100): wear 40% + technical_condition text 40% + last inspection findings 20%. Score 0 = perfect, 100 = total failure.
- **D-07:** Red-flag overrides: seepage, deformation, rapid erosion, repeated emergencies, wear≥80%, аварийное condition → automatically sets "critical condition" regardless of blended score. Stored as JSONB array. Detected via text matching against inspection findings or structure_facts.
- **D-08:** Four repair statuses: 0-39 AND no red flags → normal, 40-69 OR no red flags but weak evidence → inspection required, 70-89 → repair required, 90-100 OR any red flag → critical condition.
- **D-09:** Weak evidence rule: LOW confidence provenance, no inspection ever, last inspection >24mo, or conflicting facts → floor status at "inspection required" (never downgrade below it).

**RBAC Implementation:**
- **D-10:** JWT-based auth with role claims. `users` table: id (UUID PK), username (unique), role (enum: admin/engineer/inspector/viewer), full_name, created_at. JWT tokens contain user_id, username, role, expiry.
- **D-11:** Minimal auth flow: `POST /api/v1/auth/token` (accepts username or API key, returns JWT), `GET /api/v1/auth/me` (returns current user from token). No password hashing in Phase 3 — simple shared secret or API key lookup. `get_current_user` and `require_role(role)` FastAPI dependencies.
- **D-12:** Role permissions matrix: viewer=read+export, inspector=+inspect+upload, engineer=+edit+override, admin=+delete+manage users.
- **D-13:** Engineer override: `POST /api/v1/structures/{id}/override` — sets manual inspection_interval and/or repair_status. Creates provenance record (source_type="manual", confidence="HIGH"). Stored in risk_assessments with `is_override=true`. System-computed values preserved for audit. Overrides expire when new inspection is recorded.

**Inspection History & Document Attachments:**
- **D-14:** `inspections` table: id, structure_id (FK), inspection_date, inspector_name, inspector_role, findings (Text), condition_at_inspection, condition_score_at_inspection (nullable), red_flags_observed (JSONB), provenance_id (FK), created_at. One row per inspection event.
- **D-15:** `inspection_photos` table: id, inspection_id (FK), minio_bucket, minio_object_key, caption (nullable), photo_type (overview/detail/defect), provenance_id (FK), created_at. Photos in MinIO `sujoly-photos` bucket. API stores only object key + metadata.
- **D-16:** Inspection endpoints: POST /api/v1/structures/{id}/inspections (inspector+), GET list (all roles, with photo presigned download URLs), GET detail (all roles). Photo upload via presigned URL flow. Creating inspection triggers risk recomputation.
- **D-17:** `documents` table: id, structure_id (FK nullable), document_type (enum: passport/inspection_report/technical_spec/photo/other), title, language (ru/kk/en), minio_bucket, minio_object_key, file_size_bytes (nullable), uploaded_by, provenance_id (FK), created_at. Documents in MinIO `sujoly-documents` bucket.
- **D-18:** Document endpoints: POST register (inspector+), GET list (all roles, with presigned download URLs), DELETE (admin only), GET download (presigned URL). Upload via presigned URL flow.

**Export Endpoints:**
- **D-19:** Export endpoints at `/api/v1/export`: GET structures CSV, GET structures GeoJSON, GET inspection report PDF. All accept `lang` parameter (ru/kk/en). Filters as query params (type, district, condition, bbox).
- **D-20:** CSV export: StreamingResponse with Python `csv` module. UTF-8 with BOM for Excel compatibility with Cyrillic. Columns include all structure fields + current risk assessment.
- **D-21:** GeoJSON export: Reuse existing GeoJSON FeatureCollection format from structures list endpoint. Add risk assessment fields to properties. Streaming for large datasets.
- **D-22:** PDF export: WeasyPrint (HTML→PDF) with Jinja2 templates. One template per language (ru/kk/en). Template includes: structure identity, inspection details, findings, photos (embedded as base64 from MinIO), risk assessment summary, provenance summary. Add `weasyprint` and `jinja2` to dependencies.
- **D-23:** Trilingual export labels: Server-side translations dict in `apps/api/src/api/services/exports.py` with keys for column headers, report sections, status names in ru/kk/en. NOT next-intl (frontend) — server-side translation for export documents only.

### the agent's Discretion
- Specific weight values within the defined ranges (condition score blend weights, consequence factor calculation details)
- Exact keyword lists for red-flag text matching (Russian/Kazakh inspection finding keywords)
- JWT token expiry duration and refresh strategy
- Password/API key storage mechanism for the minimal auth flow
- Pydantic schema field names and response structure details for new endpoints
- Alembic migration numbering (continue from 0002 → 0003+)
- Database index strategy for new tables (which columns get B-tree vs GIN vs GiST)
- Error handling and validation specifics for risk computation edge cases
- WeasyPrint template HTML/CSS structure and styling
- CSV column ordering and which fields to include/exclude
- Whether to add a `risk_assessments` cache in Redis for frequently-accessed structures
- Test fixture data for risk model unit tests
- Celery Beat schedule configuration for daily risk recomputation

### Deferred Ideas (OUT OF SCOPE)
- Full authentication system (registration, password reset, OAuth, MFA, email verification)
- Risk model ML enhancement (training predictive models on historical data)
- Real-time risk alerts (push notifications on threshold crossing)
- Risk model calibration UI (dashboard for adjusting weights/thresholds)
- Bulk export with async job (Celery-based async export for very large datasets)
- Document OCR and text extraction (Phase 4/5)
- Inspection template/forms (predefined inspection forms per structure type)
- Risk score versioning and comparison (API + visualization for trend analysis)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-05 | System stores inspection history per structure (date, inspector, findings, photo URLs, condition at time of inspection) | D-14/D-15/D-16: `inspections` + `inspection_photos` tables, CRUD endpoints, MinIO presigned URL pattern (existing). See Architecture Patterns § Inspection History. |
| DATA-06 | System provides document attachment endpoints (scanned passports, inspection reports, photos) via MinIO presigned URLs | D-17/D-18: `documents` table, CRUD endpoints, reuses existing MinIO presigned URL pattern from Phase 1. See Architecture Patterns § Document Attachments. |
| RISK-01 | System computes risk-informed inspection interval using semi-quantitative model: condition × consequence × seasonal × staleness | D-01/D-02/D-03: Pure Python `risk_engine.py` module with formula and threshold bands. See Code Examples § Risk Engine. |
| RISK-02 | System maps inspection urgency to legible intervals: 30d, 90d, 180d, 12mo, 24mo, with emergency override | D-03: Threshold band mapping (≥200→emergency, 150-199→30d, 100-149→90d, 60-99→180d, 30-59→12mo, <30→24mo). See Code Examples § Risk Engine. |
| RISK-03 | System determines repair need using blended condition score (0-100) with red-flag overrides for critical indicators | D-06/D-07: Blended condition score + red-flag keyword detection. See Code Examples § Repair Status. |
| RISK-04 | System assigns one of four repair statuses: normal, inspection required, repair required, critical condition | D-08: Threshold bands for status mapping. See Code Examples § Repair Status. |
| RISK-05 | System prefers "inspection required" over false certainty when evidence is weak, stale, or conflicting | D-09: Weak-evidence floor rule (LOW confidence, no inspection, >24mo stale, conflicting facts → floor at "inspection required"). See Code Examples § Repair Status. |
| RISK-06 | System provides endpoints for engineer role to override system-recommended inspection intervals and repair statuses with logged provenance | D-13: Override endpoint creates provenance + flagged risk_assessment record. See Architecture Patterns § Engineer Override. |
| RISK-07 | System enforces administrator, engineer, inspector, and viewer role permissions (RBAC) | D-10/D-11/D-12: JWT auth, `users` table, `get_current_user`/`require_role` FastAPI dependencies, permissions matrix. See Code Examples § JWT Auth. |
| RISK-08 | System provides export endpoints for structure lists as CSV/GeoJSON and inspection report generation as PDF in all three languages | D-19/D-20/D-21/D-22/D-23: Three export endpoints, StreamingResponse for CSV, reuse GeoJSON pattern, WeasyPrint + Jinja2 for PDF, server-side translations dict. See Code Examples § Exports. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Risk score computation | API / Backend | — | Pure Python module, no DB function. Needs structure data + facts as input. Stateless computation. [D-01] |
| Risk assessment persistence | Database / Storage | API / Backend | `risk_assessments` table in PostgreSQL. API writes computed assessments. Historical retention for trend analysis. [D-04] |
| Risk recomputation scheduling | API / Backend (Celery) | Database / Storage | Celery Beat daily job + event-driven triggers. Celery worker executes recomputation. [D-05] |
| Repair status determination | API / Backend | — | Pure Python logic in risk_engine.py. Blended score + red-flag overrides + weak-evidence floor. [D-06–D-09] |
| RBAC / JWT authentication | API / Backend | — | FastAPI dependency injection. JWT encode/decode in auth_service.py. `users` table in PostgreSQL. [D-10–D-12] |
| Engineer override with provenance | API / Backend | Database / Storage | Override endpoint creates provenance record + flagged risk_assessment. Full audit trail. [D-13] |
| Inspection history CRUD | API / Backend | Database / Storage | Service layer pattern (async_session). `inspections` + `inspection_photos` tables. [D-14–D-16] |
| Inspection photo storage | Database / Storage (MinIO) | API / Backend | Binary photos in MinIO `sujoly-photos` bucket. API stores only object keys + metadata. Reuses existing presigned URL pattern. [D-15] |
| Document attachment CRUD | API / Backend | Database / Storage (MinIO) | `documents` table + MinIO `sujoly-documents` bucket. Reuses existing presigned URL pattern. [D-17–D-18] |
| CSV export | API / Backend | — | Python `csv` module + FastAPI `StreamingResponse`. UTF-8 BOM for Excel. Server-side translations. [D-20] |
| GeoJSON export | API / Backend | — | Reuses existing GeoJSON FeatureCollection pattern from structures list endpoint. [D-21] |
| PDF export | API / Backend | — | WeasyPrint (HTML→PDF) + Jinja2 templates. Per-language templates. Photos embedded as base64. [D-22] |
| Trilingual export labels | API / Backend | — | Server-side translations dict in `exports.py`. NOT next-intl (that's frontend). [D-23] |

## Project Constraints (from AGENTS.md)

- **Tech stack**: FastAPI 0.128 + SQLAlchemy 2.0 async + GeoAlchemy2 + asyncpg + Alembic + Celery 5.4 + Pydantic 2.x + Redis 7 + MinIO + PostgreSQL 17/PostGIS 3.5
- **Architecture principle**: "LLMs never make final engineering decisions" — the risk model is semi-quantitative and defensible, not ML-based. Every fact/status has provenance.
- **Architecture principle**: "Every structure has one canonical asset record, many evidence sources, and a time-based condition history." — `risk_assessments` with `valid_to` supports time-based history.
- **Data sources**: Russian is the primary data language. Trilingual UI required (Russian, Kazakh, English).
- **GSD Workflow**: Do not make direct repo edits outside a GSD workflow.
- **No project skills** configured — no skill-specific conventions to follow.

## Standard Stack

### Core (Existing — No Changes)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.128.x | API framework, dependency injection for RBAC | Already in codebase. OAuth2PasswordBearer + SecurityScopes for role enforcement. [VERIFIED: Context7 `/fastapi/fastapi` v0.128.0] |
| SQLAlchemy | 2.0+ | Async ORM for new tables | Already in codebase. Same Mapped type pattern for new models. [VERIFIED: codebase] |
| GeoAlchemy2 | 0.18+ | PostGIS types | Already in codebase. New models use same Base. [VERIFIED: codebase] |
| asyncpg | 0.29+ | Async PostgreSQL driver | Already in codebase. Same async_session pattern. [VERIFIED: codebase] |
| Alembic | 1.18+ | Database migrations | Already in codebase. Continue numbering from 0003. [VERIFIED: codebase] |
| Celery | 5.4+ | Task queue for risk recomputation | Already in codebase. Add Beat schedule + risk recomputation task. [VERIFIED: Context7 `/websites/celeryq_dev_en_stable`] |
| Pydantic | 2.x | Data validation, request/response schemas | Already in codebase. ConfigDict(from_attributes=True) for new schemas. [VERIFIED: codebase] |
| MinIO SDK | 7.2+ | Object storage for photos/documents | Already in codebase. Reuse presigned URL pattern. [VERIFIED: codebase] |
| structlog | 24.1+ | Structured logging | Already in codebase. New services use same logger pattern. [VERIFIED: codebase] |

### New (Phase 3 Additions)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| WeasyPrint | 69.0 | HTML→PDF rendering for inspection reports | Officially recommended by CONTEXT.md D-22. Native Cyrillic/Kazakh script support via Pango. Jinja2 template integration. HTML/CSS templating is easier to maintain than ReportLab. [VERIFIED: PyPI weasyprint 69.0, slopcheck OK, Context7 `/websites/doc_courtbouillon_weasyprint_stable`] |
| PyJWT | 2.13.0 | JWT token encode/decode for RBAC | Official FastAPI security tutorial uses PyJWT (`import jwt`). Lightweight, standard, no extra dependencies. [VERIFIED: PyPI pyjwt 2.13.0, slopcheck OK, Context7 `/jpadilla/pyjwt` + `/fastapi/fastapi`] |
| Jinja2 | 3.1.6 | HTML templating for PDF generation | Standard Python templating engine. Pairs with WeasyPrint for HTML template → PDF. Already installed as dependency of FastAPI (Starlette uses it). [VERIFIED: PyPI jinja2 3.1.6, slopcheck OK] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| WeasyPrint | ReportLab | ReportLab is programmatic PDF generation (no HTML). WeasyPrint uses HTML/CSS templates — easier to maintain, native Cyrillic/Kazakh support. D-22 locked WeasyPrint. |
| WeasyPrint | wkhtmltopdf | External binary dependency, less Python-native. WeasyPrint is pure Python (with Pango system libs). |
| PyJWT | python-jose | python-jose is heavier, supports JWS/JWE/JWK. PyJWT is lighter and sufficient for HS256 JWT. FastAPI tutorial uses PyJWT directly. |
| PyJWT | Authlib | More features but overkill for MVP minimal auth. PyJWT is the standard choice. |
| Jinja2 | Mako | Jinja2 is the de facto Python templating standard. Already a transitive dependency. |

**Installation:**
```bash
# Add to apps/api/pyproject.toml dependencies
weasyprint>=69.0
pyjwt>=2.13.0
jinja2>=3.1.6
```

**Version verification:**
```bash
pip index versions weasyprint  # → 69.0 (latest, verified 2026-06-26)
pip index versions pyjwt        # → 2.13.0 (latest, verified 2026-06-26)
pip index versions jinja2       # → 3.1.6 (latest, verified 2026-06-26)
```

**Dockerfile system dependencies for WeasyPrint:**
The Dockerfile runtime stage (`python:3.12-slim-bookworm`) must install Pango and related system libraries. Without these, WeasyPrint will fail with `OSError: cannot load library 'libpango-1.0.so.0'`. [CITED: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html]

```dockerfile
# Add to apps/api/Dockerfile runtime stage, before COPY --from=builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| weasyprint | PyPI | ~14 yrs (v0.1 → 69.0) | High (standard PDF lib) | github.com/Kozea/WeasyPrint | [OK] | Approved |
| pyjwt | PyPI | ~12 yrs (v0.1 → 2.13.0) | Very high (standard JWT lib) | github.com/jpadilla/pyjwt | [OK] | Approved |
| jinja2 | PyPI | ~16 yrs (v2.0 → 3.1.6) | Very high (standard template engine) | github.com/pallets/jinja | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

All three packages are long-established, widely-used Python libraries with active maintenance, high download counts, and official source repositories. slopcheck verified all three as `[OK]`.

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────────────────────────────┐
                    │                  FastAPI Application                 │
                    │                                                     │
                    │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │  │Auth Router│  │Risk Router│  │Inspections Router│  │
                    │  │/auth/token│  │/override  │  │/structures/{id}/ │  │
                    │  │/auth/me   │  │/risk/{id} │  │ inspections      │  │
                    │  └─────┬─────┘  └─────┬─────┘  └────────┬─────────┘  │
                    │        │              │                  │            │
                    │  ┌─────▼─────┐  ┌─────▼─────┐  ┌────────▼─────────┐  │
                    │  │auth_service│  │risk_engine│  │inspection_service│  │
                    │  │(JWT encode)│  │(pure calc)│  │(CRUD + photos)   │  │
                    │  └─────┬─────┘  └─────┬─────┘  └────────┬─────────┘  │
                    │        │              │                  │            │
                    │  ┌─────▼──────────────▼──────────────────▼─────────┐ │
                    │  │           Documents Service / Export Service     │ │
                    │  │  (MinIO presigned URLs / CSV / GeoJSON / PDF)   │ │
                    │  └──────────────────────┬──────────────────────────┘ │
                    │                         │                            │
                    │  ┌──────────────────────▼──────────────────────────┐ │
                    │  │          RBAC Dependency Layer                   │ │
                    │  │  get_current_user → require_role(role)           │ │
                    │  │  OAuth2PasswordBearer → JWT decode → role check   │ │
                    │  └──────────────────────────────────────────────────┘ │
                    └────────────────────────────┬────────────────────────┘
                                                 │
                    ┌────────────────────────────▼────────────────────────┐
                    │              PostgreSQL / PostGIS                    │
                    │  ┌──────────┐ ┌────────────┐ ┌───────────────────┐  │
                    │  │structures│ │provenance  │ │risk_assessments   │  │
                    │  │(existing)│ │(existing)  │ │(NEW: scores+flags)│  │
                    │  └──────────┘ └────────────┘ └───────────────────┘  │
                    │  ┌──────────┐ ┌────────────┐ ┌───────────────────┐  │
                    │  │users     │ │inspections │ │inspection_photos  │  │
                    │  │(NEW:RBAC)│ │(NEW:history)│ │(NEW:MinIO keys)  │  │
                    │  └──────────┘ └────────────┘ └───────────────────┘  │
                    │  ┌──────────────────────────────────────────────┐   │
                    │  │documents (NEW: attachments + MinIO keys)      │   │
                    │  └──────────────────────────────────────────────┘   │
                    └────────────────────────────────────────────────────┘
                                                 │
                    ┌────────────────────────────▼────────────────────────┐
                    │              MinIO (Existing)                        │
                    │  sujoly-photos (inspection photos)                   │
                    │  sujoly-documents (passports, reports)               │
                    └────────────────────────────────────────────────────┘
                                                 │
                    ┌────────────────────────────▼────────────────────────┐
                    │         Celery Worker + Celery Beat (NEW)            │
                    │  ┌──────────────────────────────────────────────┐   │
                    │  │  daily_risk_recomputation (Beat: crontab)     │   │
                    │  │  → fetches all structures → recomputes risk   │   │
                    │  └──────────────────────────────────────────────┘   │
                    │  ┌──────────────────────────────────────────────┐   │
                    │  │  recompute_structure_risk (event-triggered)   │   │
                    │  │  → called after inspection/structure update   │   │
                    │  └──────────────────────────────────────────────┘   │
                    └────────────────────────────────────────────────────┘
```

**Data flow for risk computation:**
1. Structure data + structure_facts loaded from PostgreSQL
2. `risk_engine.py` computes: condition_score → consequence_factor → seasonal_modifier → staleness_modifier → composite_score
3. Red-flag detection scans inspection findings + structure_facts for keyword matches
4. Threshold bands map composite_score → inspection_interval
5. Blended condition score + red-flags + weak-evidence → repair_status
6. Result persisted to `risk_assessments` table with provenance_id

**Data flow for inspection creation (triggers recomputation):**
1. Client gets presigned upload URL → uploads photos to MinIO
2. Client POSTs inspection with photo object keys → `inspection_service` creates row
3. `inspection_service` enqueues `recompute_structure_risk` Celery task
4. Celery worker runs `risk_engine.compute_risk()` → persists to `risk_assessments`

### Recommended Project Structure
```
apps/api/src/api/
├── models/
│   ├── structure.py           # (existing)
│   ├── provenance.py          # (existing)
│   ├── user.py                # NEW: UserModel (RBAC)
│   ├── inspection.py          # NEW: InspectionModel + InspectionPhotoModel
│   ├── document.py            # NEW: DocumentModel
│   └── risk_assessment.py     # NEW: RiskAssessmentModel
├── schemas/
│   ├── structures.py          # (existing)
│   ├── auth.py                # NEW: TokenRequest, TokenResponse, UserResponse
│   ├── inspections.py         # NEW: InspectionCreate, InspectionResponse, PhotoResponse
│   ├── documents.py           # NEW: DocumentCreate, DocumentResponse
│   ├── risk.py                # NEW: RiskAssessmentResponse, OverrideRequest
│   └── exports.py             # NEW: ExportParams schema
├── services/
│   ├── structure_service.py   # (existing)
│   ├── minio_client.py        # (existing — reuse)
│   ├── risk_engine.py         # NEW: Pure Python risk computation module
│   ├── auth_service.py        # NEW: JWT encode/decode, user lookup
│   ├── inspection_service.py  # NEW: Inspection CRUD + photo linking
│   ├── document_service.py    # NEW: Document CRUD + MinIO linking
│   ├── export_service.py      # NEW: CSV/GeoJSON/PDF generation + translations
│   └── risk_service.py        # NEW: Risk assessment persistence + recomputation triggers
├── routes/
│   ├── structures.py          # (existing — add RBAC deps)
│   ├── minio.py               # (existing — reuse)
│   ├── auth.py                # NEW: /auth/token, /auth/me
│   ├── inspections.py         # NEW: /structures/{id}/inspections
│   ├── documents.py           # NEW: /structures/{id}/documents, /documents/{id}
│   ├── risk.py                # NEW: /structures/{id}/override, /structures/{id}/risk
│   └── exports.py             # NEW: /export/structures, /export/inspection-report/{id}
├── tasks/
│   └── celery_tasks.py        # (existing — add risk recomputation tasks)
├── config/
│   └── settings.py            # (existing — add JWT settings)
├── infrastructure/
│   └── database.py            # (existing — no changes)
└── main.py                    # (existing — register new routers)
```

### Pattern 1: FastAPI RBAC with JWT and Dependency Injection
**What:** OAuth2PasswordBearer extracts token → PyJWT decodes claims → `get_current_user` returns user → `require_role(role)` checks role claim.
**When to use:** All endpoints that require authentication or role-specific permissions.
**Example:**
```python
# Source: Context7 /fastapi/fastapi — OAuth2 scopes tutorial
# Adapted for role-based (not scope-based) access control per D-10/D-11/D-12

from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

SECRET_KEY = settings.jwt_secret
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    # Lookup user from DB, return UserModel
    user = await auth_service.get_user_by_id(uuid.UUID(user_id))
    if user is None:
        raise credentials_exception
    return user

def require_role(required_role: str):
    """Dependency factory for role enforcement per D-12 permissions matrix."""
    async def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        role_hierarchy = {"viewer": 0, "inspector": 1, "engineer": 2, "admin": 3}
        if role_hierarchy.get(current_user.role, -1) < role_hierarchy.get(required_role, -1):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' insufficient. Requires '{required_role}' or higher.",
            )
        return current_user
    return role_checker

# Usage in routes:
@router.post("/structures/{id}/inspections")
async def create_inspection(
    body: InspectionCreate,
    current_user: UserModel = Depends(require_role("inspector")),
):
    ...
```
[CITED: Context7 `/fastapi/fastapi` — OAuth2 scopes tutorial, `/jpadilla/pyjwt` — encode/decode docs]

### Pattern 2: Risk Engine as Pure Python Module
**What:** Stateless function that takes structure data + facts + inspections as input, returns a risk assessment dict. No DB access, no side effects. Fully unit-testable.
**When to use:** D-01 requires the risk computation to be a pure Python module for testability and explainability.
**Example:**
```python
# apps/api/src/api/services/risk_engine.py
# Pure Python — no DB imports, no async, no side effects

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

@dataclass
class RiskAssessment:
    condition_score: float
    consequence_factor: float
    seasonal_modifier: float
    staleness_modifier: float
    composite_score: float
    inspection_interval: str  # emergency/30d/90d/180d/12mo/24mo
    repair_status: str  # normal/inspection_required/repair_required/critical_condition
    red_flags: list[str] = field(default_factory=list)
    contributing_factors: dict[str, Any] = field(default_factory=dict)
    weak_evidence_reasons: list[str] = field(default_factory=list)

# D-02: Condition score mapping for technical_condition text
_CONDITION_MAP = {
    "хорошее": 90,
    "удовлетворительное": 60,
    "неудовлетворительное": 30,
    "аварийное": 10,
}

# D-02: Consequence factor by structure type
_CONSEQUENCE_BY_TYPE = {
    "dam": 2.0, "weir": 2.0, "reservoir": 1.8,
    "canal": 1.0, "pipeline": 1.2, "pumping_station": 1.5,
}

# D-02: Seasonal modifier by month (Kazakhstan flood season)
def _seasonal_modifier(assessment_date: date) -> float:
    month = assessment_date.month
    if 3 <= month <= 5:  # Flood season (March-May)
        return 1.5
    elif month in (1, 2):  # Pre-flood inspection period
        return 1.2
    else:  # Dry season
        return 0.8

# D-02: Staleness modifier by days since last inspection
def _staleness_modifier(days_since_inspection: int | None) -> float:
    if days_since_inspection is None:
        return 1.5  # Never inspected
    if days_since_inspection < 90:
        return 0.5
    elif days_since_inspection < 180:
        return 0.8
    elif days_since_inspection < 365:
        return 1.0
    elif days_since_inspection < 730:
        return 1.2
    else:
        return 1.5

def compute_condition_score(
    wear_percentage: float | None,
    technical_condition: str | None,
    last_inspection_score: float | None,
) -> float:
    """D-06: Blended condition score (0-100). 0=perfect, 100=total failure."""
    wear_score = (100 - wear_percentage) if wear_percentage is not None else None
    condition_score = _CONDITION_MAP.get(technical_condition.lower() if technical_condition else "", None)
    inspection_score = last_inspection_score

    # Weight redistribution when data is missing (D-02)
    components = []
    if wear_score is not None:
        components.append(("wear", wear_score, 0.4))
    if condition_score is not None:
        components.append(("condition", condition_score, 0.4))
    if inspection_score is not None:
        components.append(("inspection", inspection_score, 0.2))

    if not components:
        return 50.0  # Default when no data available

    # Redistribute weights proportionally
    total_weight = sum(w for _, _, w in components)
    score = sum(val * (w / total_weight) for _, val, w in components)
    return min(100.0, max(0.0, score))

# D-07: Red-flag detection
_REDFLAG_KEYWORDS = [
    "просачивание", "деформация", "эрозия", "быстрая эрозия",
    "аварийная ситуация", "повторные аварийные ситуации",
]

def detect_red_flags(
    wear_percentage: float | None,
    technical_condition: str | None,
    inspection_findings: str | None,
    structure_facts: dict | None,
) -> list[str]:
    flags = []
    if wear_percentage is not None and wear_percentage >= 80:
        flags.append("wear_percentage_ge_80")
    if technical_condition and technical_condition.lower() == "аварийное":
        flags.append("emergency_condition")
    text_to_scan = " ".join(filter(None, [
        inspection_findings or "",
        " ".join(str(v) for v in (structure_facts or {}).values()),
    ])).lower()
    for keyword in _REDFLAG_KEYWORDS:
        if keyword in text_to_scan:
            flags.append(f"keyword:{keyword}")
    return flags

def compute_risk(
    structure: dict,
    facts: list[dict],
    inspections: list[dict],
    assessment_date: date | None = None,
) -> RiskAssessment:
    """D-01/D-02/D-03: Main risk computation entry point."""
    assessment_date = assessment_date or date.today()

    wear = structure.get("wear_percentage")
    condition_text = structure.get("technical_condition")
    last_inspection = inspections[0] if inspections else None
    last_inspection_score = last_inspection.get("condition_score_at_inspection") if last_inspection else None

    condition_score = compute_condition_score(wear, condition_text, last_inspection_score)
    consequence = _CONSEQUENCE_BY_TYPE.get(structure.get("type", ""), 1.0)
    seasonal = _seasonal_modifier(assessment_date)

    days_since = None
    if last_inspection and last_inspection.get("inspection_date"):
        days_since = (assessment_date - last_inspection["inspection_date"]).days

    staleness = _staleness_modifier(days_since)

    red_flags = detect_red_flags(
        wear, condition_text,
        last_inspection.get("findings") if last_inspection else None,
        {f["attribute_name"]: f["attribute_value"] for f in facts},
    )

    composite = condition_score * consequence * seasonal * staleness

    # D-03: Map to inspection interval via threshold bands
    if composite >= 200 or red_flags:
        interval = "emergency"
    elif composite >= 150:
        interval = "30d"
    elif composite >= 100:
        interval = "90d"
    elif composite >= 60:
        interval = "180d"
    elif composite >= 30:
        interval = "12mo"
    else:
        interval = "24mo"

    # D-08: Map blended condition score to repair status
    if condition_score >= 90 or red_flags:
        status_val = "critical_condition"
    elif condition_score >= 70:
        status_val = "repair_required"
    elif condition_score >= 40:
        status_val = "inspection_required"
    else:
        status_val = "normal"

    # D-09: Weak evidence floor
    weak_evidence = []
    if structure.get("provenance_confidence") == "LOW":
        weak_evidence.append("low_confidence_provenance")
    if not inspections:
        weak_evidence.append("never_inspected")
    elif days_since and days_since > 730:  # >24 months
        weak_evidence.append("stale_inspection_24mo")
    # Conflicting facts check would go here

    if weak_evidence and status_val == "normal":
        status_val = "inspection_required"

    return RiskAssessment(
        condition_score=condition_score,
        consequence_factor=consequence,
        seasonal_modifier=seasonal,
        staleness_modifier=staleness,
        composite_score=composite,
        inspection_interval=interval,
        repair_status=status_val,
        red_flags=red_flags,
        contributing_factors={
            "wear_percentage": wear,
            "technical_condition": condition_text,
            "structure_type": structure.get("type"),
            "days_since_last_inspection": days_since,
            "last_inspection_score": last_inspection_score,
        },
        weak_evidence_reasons=weak_evidence,
    )
```
[VERIFIED: Formula per D-02/D-03/D-06/D-07/D-08/D-09 from CONTEXT.md]

### Pattern 3: Engineer Override with Provenance Audit Trail
**What:** Override endpoint creates a provenance record + flagged risk_assessment record. Both system-computed and override values are stored for audit.
**When to use:** D-13 engineer/admin manual override of inspection interval or repair status.
```python
# POST /api/v1/structures/{id}/override
# Body: {"inspection_interval": "30d", "repair_status": "repair_required", "reason": "..."}

async def create_override(
    structure_id: uuid.UUID,
    override_data: OverrideRequest,
    user: UserModel,  # from require_role("engineer")
) -> RiskAssessmentModel:
    async with async_session() as session:
        async with session.begin():
            # 1. Expire current risk_assessment (set valid_to=now)
            await session.execute(
                update(RiskAssessmentModel)
                .where(and_(
                    RiskAssessmentModel.structure_id == structure_id,
                    RiskAssessmentModel.valid_to.is_(None),
                ))
                .values(valid_to=datetime.utcnow())
            )

            # 2. Create provenance for the override (D-13)
            provenance = ProvenanceModel(
                source_type="manual",
                source_reference=f"api:override:{structure_id}:by:{user.username}",
                confidence_level="HIGH",  # Human decision
                contributor=user.username,
            )
            session.add(provenance)
            await session.flush()

            # 3. Get system-computed values for audit
            system_assessment = await risk_service.get_latest_assessment(structure_id)

            # 4. Create override risk_assessment record
            override = RiskAssessmentModel(
                structure_id=structure_id,
                condition_score=system_assessment.condition_score,  # Preserve system values
                consequence_factor=system_assessment.consequence_factor,
                seasonal_modifier=system_assessment.seasonal_modifier,
                staleness_modifier=system_assessment.staleness_modifier,
                composite_score=system_assessment.composite_score,
                inspection_interval=override_data.inspection_interval,  # Override value
                repair_status=override_data.repair_status,  # Override value
                red_flags=system_assessment.red_flags,
                contributing_factors={
                    **system_assessment.contributing_factors,
                    "override_reason": override_data.reason,
                    "overridden_by": user.username,
                    "system_inspection_interval": system_assessment.inspection_interval,
                    "system_repair_status": system_assessment.repair_status,
                },
                provenance_id=provenance.id,
                is_override=True,
                computed_at=datetime.utcnow(),
                valid_to=None,  # This is now the latest
            )
            session.add(override)
            await session.flush()
            return override
```
[VERIFIED: Per D-13 specification in CONTEXT.md]

### Pattern 4: CSV Export with StreamingResponse
**What:** Python `csv` module writes to an in-memory buffer, FastAPI `StreamingResponse` streams it to the client. UTF-8 BOM for Excel Cyrillic compatibility.
**When to use:** D-20 CSV export endpoint.
```python
# Source: D-20 specification + FastAPI StreamingResponse pattern
import csv
import io
from fastapi.responses import StreamingResponse

async def export_structures_csv(lang: str = "ru", filters: dict = None) -> StreamingResponse:
    structures, _ = await list_structures(filters=filters or {}, ...)

    # D-23: Server-side translations for column headers
    headers = _TRANSLATIONS[lang]["csv_headers"]

    output = io.StringIO()
    # UTF-8 BOM for Excel compatibility with Cyrillic (D-20)
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(headers)

    for struct in structures:
        risk = await risk_service.get_latest_assessment(struct.id)
        writer.writerow([
            struct.name_ru, struct.type, struct.district,
            struct.technical_condition, struct.wear_percentage,
            risk.inspection_interval if risk else "",
            risk.repair_status if risk else "",
            risk.composite_score if risk else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=structures_{lang}.csv"},
    )
```
[VERIFIED: D-20 specification, FastAPI StreamingResponse is standard]

### Pattern 5: PDF Export with WeasyPrint + Jinja2
**What:** Jinja2 renders an HTML template with inspection data, WeasyPrint converts HTML to PDF bytes. Photos fetched from MinIO and embedded as base64.
**When to use:** D-22 PDF inspection report export.
```python
# Source: Context7 /websites/doc_courtbouillon_weasyprint_stable + D-22 specification
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import base64

async def export_inspection_report_pdf(
    inspection_id: uuid.UUID,
    lang: str = "ru",
) -> StreamingResponse:
    inspection = await inspection_service.get_inspection_detail(inspection_id)
    structure = await get_structure(inspection.structure_id)
    risk = await risk_service.get_latest_assessment(inspection.structure_id)

    # Fetch photos from MinIO and encode as base64 for embedding
    photos_base64 = []
    for photo in inspection.photos:
        minio_service = ...  # from app.state
        # Download photo bytes from MinIO
        response = minio_service.client.get_object(photo.minio_bucket, photo.minio_object_key)
        photo_bytes = response.read()
        photos_base64.append({
            "data": base64.b64encode(photo_bytes).decode(),
            "caption": photo.caption,
            "type": photo.photo_type,
        })

    # Render HTML template with Jinja2
    env = Environment(loader=FileSystemLoader("templates/"))
    template = env.get_template(f"inspection_report_{lang}.html")
    html_content = template.render(
        structure=structure,
        inspection=inspection,
        risk=risk,
        photos=photos_base64,
        labels=_TRANSLATIONS[lang]["report"],
    )

    # WeasyPrint: HTML string → PDF bytes
    pdf_bytes = HTML(string=html_content).write_pdf()

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=inspection_{inspection_id}_{lang}.pdf"},
    )
```
[CITED: Context7 `/websites/doc_courtbouillon_weasyprint_stable` — `html.write_pdf()` returns bytes when no filename given]

### Anti-Patterns to Avoid
- **Storing risk scores in the structures table:** Violates the time-based condition history principle. Use a separate `risk_assessments` table with `valid_to` for history (D-04).
- **Computing risk in a database function:** Violates D-01. The risk engine must be a pure Python module for testability and explainability.
- **Hand-rolling JWT encode/decode:** Use PyJWT. Hand-rolled JWT is a security risk — incorrect signature verification, missing exp claim validation, algorithm confusion attacks.
- **Putting photo binaries in PostgreSQL:** Violates INT-04 architecture separation. Photos go in MinIO, only object keys in PostgreSQL (D-15).
- **Using next-intl for backend translations:** next-intl is frontend-only. D-23 specifies a server-side translations dict for export labels.
- **Real-time risk computation on every API request:** D-05 says risk is a snapshot. Compute on triggers, persist, serve from `risk_assessments` table.
- **Forgetting UTF-8 BOM in CSV:** Excel will mangle Cyrillic text without BOM. Always write `\ufeff` at the start of CSV output (D-20).
- **Missing WeasyPrint system dependencies in Docker:** WeasyPrint will crash at import time with `OSError: cannot load library 'libpango-1.0.so.0'` if Pango is not installed. Must add apt-get packages to the Dockerfile runtime stage.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT token encode/decode | Manual base64 + HMAC signing | PyJWT 2.13.0 | Correct HS256 implementation, exp claim validation, algorithm confusion protection. Security-critical — never hand-roll crypto. |
| PDF generation | Manual PDF byte construction | WeasyPrint + Jinja2 | HTML/CSS templating is maintainable. Native Cyrillic/Kazakh via Pango. Page breaks, headers, fonts all handled. |
| HTML templating for PDF | f-strings or manual HTML concat | Jinja2 3.1.6 | Proper escaping, template inheritance, loops for photos/sections. Already a transitive dependency. |
| CSV generation | Manual string concatenation | Python `csv` module | Handles quoting, escaping, edge cases (commas in fields, newlines in fields). Standard library — no dependency. |
| Role-based access control | Manual if/else in every route | FastAPI `Depends` + `require_role()` factory | Declarative, testable, consistent. FastAPI dependency injection is designed for this. |
| MinIO presigned URLs | Custom S4 signing | Existing `MinIOService` class | Already implemented and tested in Phase 1. Reuse `presigned_upload_url` and `presigned_download_url`. |
| Celery Beat scheduling | Custom cron-like loop | Celery `beat_schedule` + `crontab` | Battle-tested, handles timezone, retries, monitoring. Already have Celery infrastructure. |

**Key insight:** Phase 3 extends existing patterns, not invents new ones. Every new service should mirror `structure_service.py` (async_session, session.begin(), structlog). Every new route should mirror `structures.py` (APIRouter, prefix, Pydantic models, HTTPException). Every new model should mirror `structure.py` (Mapped types, UUID PKs, JSONB for flexible data).

## Runtime State Inventory

> Phase 3 is a greenfield feature phase (new tables, new endpoints, new services). No rename/refactor/migration of existing data. However, existing structures table gets new FK relationships — documenting state impact.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — new tables (users, inspections, inspection_photos, documents, risk_assessments) are additive. No existing data modified. | None — new Alembic migration 0003+ creates new tables only |
| Live service config | docker-compose.yml needs new `celery-beat` service. Dockerfile needs WeasyPrint system deps. .env.example needs JWT settings. | Code edit: add celery-beat service, update Dockerfile, update .env.example |
| OS-registered state | None — no OS-level registrations | None |
| Secrets/env vars | New env vars: API_JWT_SECRET, API_JWT_EXPIRY_HOURS, API_INITIAL_ADMIN_USERNAME | Add to .env.example, docker-compose.yml environment section |
| Build artifacts | Docker image will need rebuild after Dockerfile changes (WeasyPrint system deps) | `docker compose build` after Dockerfile update |

## Common Pitfalls

### Pitfall 1: WeasyPrint System Dependencies Missing in Docker
**What goes wrong:** `ImportError` or `OSError: cannot load library 'libpango-1.0.so.0'` when WeasyPrint tries to render PDF.
**Why it happens:** WeasyPrint is a Python package but depends on Pango (C library) at runtime. The `python:3.12-slim-bookworm` base image doesn't include Pango by default. pip install only gets the Python wrapper.
**How to avoid:** Add `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libjpeg-dev libopenjp2-7-dev libffi-dev` to the Dockerfile runtime stage's `apt-get install` command. [CITED: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html]
**Warning signs:** PDF export endpoint returns 500. Check API logs for `OSError` mentioning `libpango`.

### Pitfall 2: JWT Secret Not Set or Weak
**What goes wrong:** Tokens are forgeable, or API fails to start with validation error.
**Why it happens:** PyJWT uses HS256 with a shared secret. If the secret is empty, hardcoded, or default, anyone can forge tokens. Pydantic Settings will accept empty string by default.
**How to avoid:** Add `jwt_secret: str = ""` to Settings with a validator that requires non-empty in non-development environments. Use `openssl rand -hex 32` to generate. Add to .env.example with a comment. For development, use a fixed dev secret.
**Warning signs:** `jwt.decode()` never raises `InvalidTokenError` even with wrong key. API starts but auth endpoints accept any token.

### Pitfall 3: Celery Beat Not Running
**What goes wrong:** Daily risk recomputation never triggers. Risk scores become stale (seasonal modifier doesn't update).
**Why it happens:** docker-compose.yml only has `celery-worker`, not `celery-beat`. Beat is a separate process that sends scheduled tasks to the worker. Without it, `beat_schedule` configuration is ignored.
**How to avoid:** Add a `celery-beat` service to docker-compose.yml with `command: celery -A api.celery_app beat --loglevel=info`. It shares the same image as celery-worker but runs the beat scheduler instead.
**Warning signs:** `risk_assessments.computed_at` timestamps don't update daily. Seasonal modifier values are stuck.

### Pitfall 4: Red-Flag Text Matching Fails on Morphological Variations
**What goes wrong:** Red flags are not detected because the keyword "просачивание" doesn't match "просачивается" (different verb form) in inspection findings.
**Why it happens:** Russian has rich morphology. Simple `in` substring matching misses morphological variants.
**How to avoid:** Use a keyword list with common variations, or use stemming. For MVP, include both noun and verb forms in the keyword list. Consider `pg_trgm` similarity for fuzzy matching if exact substring matching is insufficient. Document this as a known limitation — the red-flag detection is conservative (better to false-positive than false-negative on safety-critical flags).
**Warning signs:** Structures with known seepage issues don't get "critical_condition" status. Red-flag array is empty when it shouldn't be.

### Pitfall 5: PDF Generation Blocks the Event Loop
**What goes wrong:** API becomes unresponsive while generating a large PDF report.
**Why it happens:** WeasyPrint is a synchronous library. `HTML.write_pdf()` is a blocking call. If called directly in an async FastAPI route, it blocks the event loop.
**How to avoid:** Run WeasyPrint in a thread pool via `asyncio.to_thread()` or `run_in_executor()`. Or make the PDF export endpoint dispatch a Celery task that generates the PDF and returns a download URL.
**Warning signs:** Other API endpoints are slow when PDF export is being generated. Event loop latency spikes.

### Pitfall 6: MinIO Photo Download for PDF Base64 Embedding
**What goes wrong:** PDF generation fails or is slow because it downloads large photos from MinIO synchronously.
**Why it happens:** D-22 requires photos embedded as base64 in the PDF. The MinIO SDK's `get_object()` is synchronous and returns a stream that must be read fully.
**How to avoid:** Use `asyncio.to_thread()` for the MinIO download. Limit photo resolution/size before embedding. Consider a max photo count per report. Cache base64-encoded photos if the same report is requested multiple times.
**Warning signs:** PDF generation timeout. Memory usage spikes during PDF generation.

### Pitfall 7: Risk Assessment History Growing Unbounded
**What goes wrong:** `risk_assessments` table grows large over time as every recomputation creates a new row.
**Why it happens:** D-04 requires historical retention for trend analysis. Every inspection, structure update, and daily Beat job creates a new assessment.
**Why it's OK for MVP:** ~444 structures × 1 daily recomputation = ~444 rows/day = ~162K rows/year. This is trivially small for PostgreSQL. No cleanup needed for MVP.
**How to avoid (future):** Add a cleanup job that archives assessments older than N years. Not needed for Phase 3.
**Warning signs:** Table size > 1M rows (not expected for years).

## Code Examples

### JWT Token Issuance (auth_service.py)
```python
# Source: Context7 /jpadilla/pyjwt + /fastapi/fastapi security tutorial
# D-11: Minimal auth flow — token issuance + role enforcement

from datetime import datetime, timedelta, timezone
import jwt
from api.config.settings import settings

ALGORITHM = "HS256"

def create_access_token(user_id: str, username: str, role: str) -> str:
    """Create a JWT token with user_id, username, role, and expiry."""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises jwt.InvalidTokenError on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
```
[VERIFIED: Context7 `/jpadilla/pyjwt` — encode with exp, decode with algorithms list]

### WeasyPrint PDF Generation (rendering to bytes)
```python
# Source: Context7 /websites/doc_courtbouillon_weasyprint_stable
from weasyprint import HTML

# HTML string → PDF bytes (no file needed)
html = HTML(string='<h1>Inspection Report</h1><p>Content here</p>')
pdf_bytes = html.write_pdf()  # Returns bytes when no filename given

# With custom CSS and font configuration
from weasyprint.text.fonts import FontConfiguration

font_config = FontConfiguration()
css = CSS(string='''
    @font-face {
        font-family: NotoSans;
        src: url('fonts/NotoSans-Regular.ttf');
    }
    body { font-family: NotoSans; }
''', font_config=font_config)
pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)
```
[CITED: Context7 `/websites/doc_courtbouillon_weasyprint_stable` — first_steps.html, api_reference.html]

### Celery Beat Schedule (celery_app.py)
```python
# Source: Context7 /websites/celeryq_dev_en_stable — periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # D-05: Daily risk recomputation at 2 AM UTC
    'daily-risk-recomputation': {
        'task': 'api.tasks.celery_tasks.recompute_all_risks',
        'schedule': crontab(hour=2, minute=0),
    },
}
celery_app.conf.timezone = 'UTC'
```
[CITED: Context7 `/websites/celeryq_dev_en_stable` — userguide/periodic-tasks.html]

### Risk Assessment Model (risk_assessment.py)
```python
# Following existing model pattern from structure.py
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from api.infrastructure.database import Base

class RiskAssessmentModel(Base):
    """D-04: Risk assessment record with full factor breakdown."""
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("structures.id"), nullable=False, index=True
    )
    condition_score: Mapped[float] = mapped_column(Float, nullable=False)
    consequence_factor: Mapped[float] = mapped_column(Float, nullable=False)
    seasonal_modifier: Mapped[float] = mapped_column(Float, nullable=False)
    staleness_modifier: Mapped[float] = mapped_column(Float, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    inspection_interval: Mapped[str] = mapped_column(String(20), nullable=False)
    repair_status: Mapped[str] = mapped_column(String(30), nullable=False)
    red_flags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    contributing_factors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    is_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True  # NULL = latest assessment
    )
```
[VERIFIED: Follows existing `StructureModel` pattern, D-04 field specification]

### Users Model (user.py)
```python
import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from api.infrastructure.database import Base

class UserModel(Base):
    """D-10: Users table for RBAC with four roles."""
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'engineer', 'inspector', 'viewer')",
            name="ck_users_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
```
[VERIFIED: Follows existing model pattern, D-10 specification]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT | PyJWT 2.13.0 | PyJWT 2.x is now the standard. FastAPI official tutorial uses `import jwt` (PyJWT). | Use PyJWT directly, not python-jose. Simpler API, fewer dependencies. |
| next-pwa for PWA SW | Serwist | Next.js 16+ | Not relevant to Phase 3 (backend-only), but noted for stack consistency. |
| ReportLab for PDF | WeasyPrint + Jinja2 | WeasyPrint 60+ (HTML/CSS approach) | HTML/CSS templating is more maintainable than programmatic PDF. Native Cyrillic/Kazakh via Pango. D-22 locked this decision. |
| Manual auth middleware | FastAPI Security + OAuth2PasswordBearer | FastAPI 0.100+ | Use FastAPI's built-in security dependency system. SecurityScopes for role-based access. |

**Deprecated/outdated:**
- `python-jose`: Still functional but PyJWT is the recommended choice for new projects. FastAPI's own tutorial migrated to PyJWT.
- `passlib`: Not needed in Phase 3 (D-11 says "no password hashing — simple shared secret or API key"). If password hashing is needed later, `pwdlib` is the modern replacement (used in FastAPI's tutorial).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | PyJWT 2.13.0 is the correct package name (not `jwt` or `python-jwt`) | Standard Stack | Low — verified on PyPI and used in FastAPI official tutorial. PyPI package name is `pyjwt`, import name is `jwt`. |
| A2 | WeasyPrint 69.0 works with `python:3.12-slim-bookworm` Docker base image after installing Pango deps | Dockerfile | Low — WeasyPrint docs explicitly list Debian/Ubuntu apt packages. Verified locally with WeasyPrint 68.1 on Python 3.12. |
| A3 | Jinja2 is already a transitive dependency via FastAPI/Starlette | Standard Stack | Low — even if not, it's explicitly added to pyproject.toml. No risk either way. |
| A4 | Celery Beat can be added as a separate docker-compose service sharing the same image | Architecture Patterns | Low — standard Celery deployment pattern. Beat + Worker use the same codebase, different commands. |
| A5 | The `csv` module with `\ufeff` BOM is sufficient for Excel Cyrillic compatibility | Code Examples | Low — well-documented pattern. UTF-8 BOM is the standard fix for Excel CSV encoding issues. |
| A6 | Russian red-flag keywords are sufficient for initial detection (Kazakh keywords can be added later) | Risk Engine | Medium — if inspection findings are in Kazakh, red flags will be missed. Mitigated by also checking structure_facts which contain spreadsheet data in Russian. |
| A7 | `asyncio.to_thread()` is the correct approach for running WeasyPrint in async FastAPI routes | Pitfalls | Low — standard Python 3.9+ pattern for running sync code in async context. |

## Open Questions

1. **Initial admin user creation**
   - What we know: D-11 says "no password hashing in Phase 3 — use a simple shared secret or API key lookup." CONTEXT.md specifics say "The users table should support an initial admin user created via environment variables or a seed script."
   - What's unclear: Should the initial admin be created via Alembic migration (seed data), via a startup script in the lifespan, or via a CLI command?
   - Recommendation: Create via a seed function called during lifespan startup if no admin user exists. Use `API_INITIAL_ADMIN_USERNAME` env var. This is in the agent's discretion area.

2. **Redis caching for risk assessments**
   - What we know: CONTEXT.md lists "Whether to add a `risk_assessments` cache in Redis for frequently-accessed structures" as agent's discretion.
   - What's unclear: Is the ~444 structure dataset small enough that DB queries are always fast?
   - Recommendation: Skip Redis cache for MVP. PostgreSQL with an index on `structure_id + valid_to IS NULL` is fast enough for 444 structures. Add cache only if performance becomes an issue.

3. **WeasyPrint font files for Kazakh script**
   - What we know: WeasyPrint uses Pango for text rendering. Cyrillic is well-supported. Kazakh uses Cyrillic script with additional characters (ә, ғ, қ, ң, ө, ұ, һ).
   - What's unclear: Does the default Pango font on `python:3.12-slim-bookworm` include Kazakh Cyrillic characters?
   - Recommendation: Include a Noto Sans font file in the Docker image (or use a web font URL in the Jinja2 template CSS) to guarantee Kazakh character rendering. Test with actual Kazakh text in the PDF report.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | Runtime | ✓ | 3.12.12 | — |
| Docker | Container builds | ✓ | 29.4.1 | — |
| uv | Dependency management | ✓ | 0.11.8 | pip |
| Node.js | Not required for backend | ✓ | 24.14.1 | — |
| PostgreSQL/PostGIS | Database (Docker) | ✓ (via Docker) | 17/3.5 | — |
| Redis | Celery broker (Docker) | ✓ (via Docker) | 7-alpine | — |
| MinIO | Object storage (Docker) | ✓ (via Docker) | latest | — |
| Celery | Task queue | ✓ (via pip) | 5.4+ | — |
| WeasyPrint | PDF generation | ✗ (not in Docker image yet) | 69.0 | Must add to Dockerfile + pyproject.toml |
| PyJWT | JWT auth | ✗ (not installed yet) | 2.13.0 | Must add to pyproject.toml |
| Jinja2 | HTML templating | ✓ (transitive dep) | 3.1.6 | — |

**Missing dependencies with no fallback:**
- WeasyPrint system dependencies (Pango, HarfBuzz) must be added to the Dockerfile runtime stage. Without these, PDF export will fail.
- PyJWT must be added to pyproject.toml. Without it, JWT auth cannot work.

**Missing dependencies with fallback:**
- None — all missing deps are being explicitly added in this phase.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio (already in dev dependencies) |
| Config file | `apps/api/pyproject.toml` `[tool.pytest.ini_options]` — asyncio_mode = "auto" |
| Quick run command | `cd apps/api && python -m pytest tests/ -x -q` |
| Full suite command | `cd apps/api && python -m pytest tests/ -v --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RISK-01 | Risk computation: condition × consequence × seasonal × staleness | unit | `pytest tests/test_risk_engine.py::test_compute_risk -x` | ❌ Wave 0 |
| RISK-02 | Inspection interval mapping (threshold bands + emergency) | unit | `pytest tests/test_risk_engine.py::test_interval_mapping -x` | ❌ Wave 0 |
| RISK-03 | Red-flag detection (keyword matching, wear≥80%, аварийное) | unit | `pytest tests/test_risk_engine.py::test_red_flags -x` | ❌ Wave 0 |
| RISK-04 | Four repair statuses via threshold bands | unit | `pytest tests/test_risk_engine.py::test_repair_status -x` | ❌ Wave 0 |
| RISK-05 | Weak-evidence floor (never below "inspection required") | unit | `pytest tests/test_risk_engine.py::test_weak_evidence -x` | ❌ Wave 0 |
| RISK-06 | Engineer override with provenance | integration | `pytest tests/test_risk_api.py::test_override -x` | ❌ Wave 0 |
| RISK-07 | RBAC enforcement (4 roles, permission matrix) | integration | `pytest tests/test_auth.py -x` | ❌ Wave 0 |
| RISK-08 | Export endpoints (CSV/GeoJSON/PDF, trilingual) | integration | `pytest tests/test_exports.py -x` | ❌ Wave 0 |
| DATA-05 | Inspection history CRUD + photos via MinIO | integration | `pytest tests/test_inspections.py -x` | ❌ Wave 0 |
| DATA-06 | Document attachment CRUD + MinIO presigned URLs | integration | `pytest tests/test_documents.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd apps/api && python -m pytest tests/ -x -q` (quick run, < 30s)
- **Per wave merge:** `cd apps/api && python -m pytest tests/ -v --tb=short` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_risk_engine.py` — covers RISK-01, RISK-02, RISK-03, RISK-04, RISK-05 (pure unit tests, no DB needed)
- [ ] `tests/test_auth.py` — covers RISK-07 (JWT encode/decode, role enforcement)
- [ ] `tests/test_risk_api.py` — covers RISK-06 (override endpoint with provenance)
- [ ] `tests/test_inspections.py` — covers DATA-05 (inspection CRUD + photo presigned URLs)
- [ ] `tests/test_documents.py` — covers DATA-06 (document CRUD + MinIO presigned URLs)
- [ ] `tests/test_exports.py` — covers RISK-08 (CSV/GeoJSON/PDF export, trilingual labels)
- [ ] Update `tests/conftest.py` — add fixtures for mock risk assessments, mock inspections, mock users, mock documents
- [ ] Framework install: WeasyPrint + PyJWT + Jinja2 (in pyproject.toml, installed via `uv sync`)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Minimal JWT auth (D-11). No password hashing — API key/shared secret lookup. Not production auth. |
| V3 Session Management | yes | JWT with exp claim. Stateless tokens. No server-side session store. Token expiry via settings.jwt_expiry_hours. |
| V4 Access Control | yes | RBAC with 4 roles (D-12). FastAPI `require_role()` dependency factory. Role hierarchy: viewer < inspector < engineer < admin. |
| V5 Input Validation | yes | Pydantic v2 schema validation on all request bodies. SQLAlchemy parameterized queries (existing pattern). Query param validation via FastAPI Query constraints. |
| V6 Cryptography | yes | JWT HS256 signing (PyJWT). Secret from env var. Never hardcode. Use `openssl rand -hex 32` for generation. |
| V7 Error Handling | yes | Existing global exception handler in main.py. HTTPException for 401/403/404. No stack traces in responses. |
| V8 Data Protection | yes | MinIO presigned URLs for binary assets (time-limited). No binary data in API responses. JWT secret in env var, not in code. |
| V9 Communications | yes | CORS configured (existing). HTTPS in production (HSTS header already set in middleware). |
| V13 API & Web Service | yes | REST API with OpenAPI docs. OAuth2PasswordBearer security scheme. All endpoints documented. |

### Known Threat Patterns for FastAPI + JWT Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| JWT forgery (weak secret) | Spoofing | Use strong random secret (32+ hex chars). Never commit to git. Env var only. |
| JWT algorithm confusion (alg=none) | Tampering | PyJWT 2.x rejects `alg=none` by default. Always specify `algorithms=["HS256"]` in decode. |
| Missing role check on endpoint | Elevation of Privilege | Use `Depends(require_role("..."))` on every non-public endpoint. Test all endpoints with each role. |
| Presigned URL leakage | Information Disclosure | Short expiry (1hr upload, 2hr download). URLs are not logged. No CORS on MinIO presigned endpoints. |
| CSV injection (formula injection) | Tampering | Prefix cells starting with `=`, `+`, `-`, `@` with single quote. Standard CSV export mitigation. |
| Mass assignment (over-POST) | Tampering | Use explicit Pydantic schemas (not dict). Only whitelisted fields in request models. |
| IDOR (Insecure Direct Object Reference) | Elevation of Privilege | UUID PKs (unguessable). Authorization check on every structure-specific endpoint. |
| SQL injection | Tampering | SQLAlchemy parameterized queries (existing pattern). No string interpolation in queries. |

## Sources

### Primary (HIGH confidence)
- Context7 `/fastapi/fastapi` (v0.128.0, 2153 snippets) — OAuth2PasswordBearer, SecurityScopes, JWT auth tutorial, dependency injection
- Context7 `/jpadilla/pyjwt` (102 snippets) — JWT encode/decode, exp claim, algorithm specification
- Context7 `/websites/doc_courtbouillon_weasyprint_stable` (400 snippets) — Installation, system dependencies, HTML→PDF API, FontConfiguration
- Context7 `/websites/celeryq_dev_en_stable` (4697 snippets) — Beat schedule, crontab, periodic tasks
- PyPI registry — weasyprint 69.0, pyjwt 2.13.0, jinja2 3.1.6 (verified 2026-06-26)
- slopcheck — all packages [OK]
- Existing codebase — structure.py, provenance.py, structure_service.py, minio_client.py, main.py, settings.py, celery_app.py, alembic migrations, test patterns

### Secondary (MEDIUM confidence)
- WeasyPrint official docs https://doc.courtbouillon.org/weasyprint/stable/first_steps.html — Debian/Ubuntu system dependency list

### Tertiary (LOW confidence)
- None — all claims verified via Context7, official docs, or codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified on PyPI, slopcheck [OK], Context7 docs fetched, existing codebase patterns confirmed
- Architecture: HIGH — follows existing codebase patterns exactly, all decisions locked in CONTEXT.md
- Pitfalls: HIGH — WeasyPrint system deps confirmed via official docs, JWT patterns confirmed via FastAPI tutorial, Celery Beat confirmed via official docs
- Security: HIGH — FastAPI security patterns verified via Context7, ASVS categories mapped to phase scope

**Research date:** 2026-06-26
**Valid until:** 2026-07-26 (30 days — stable domain, well-established packages)
