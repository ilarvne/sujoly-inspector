# Phase 3: Risk Models & Inspection Logic - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-26
**Phase:** 03-risk-models-inspection-logic
**Mode:** --auto (all decisions auto-selected with recommended defaults)
**Areas discussed:** Risk Score Model Design, Repair Status Determination, RBAC Implementation, Inspection History & Document Attachments, Export Endpoints

---

## Risk Score Model Design

| Option | Description | Selected |
|--------|-------------|----------|
| Pure Python module | Risk computation in `risk_engine.py` — testable, explainable, no DB coupling | ✓ |
| Database function | PostgreSQL stored procedure — fast but harder to test/debug | |
| Hybrid (Python + DB cache) | Python computation with materialized view cache | |

**Auto-selected:** Pure Python module (recommended)
**Notes:** Aligns with "semi-quantitative, defensible" principle. Module takes structure data + facts as input, returns risk assessment with interval, score breakdown, and contributing factors.

| Option | Description | Selected |
|--------|-------------|----------|
| Condition 40%/40%/20%, consequence 0.5-2.0, seasonal 0.8-1.5, staleness 0.5-1.5 | Covers RISK-01 factors with defensible ranges | ✓ |
| Equal weights (25% each) | Simpler but less nuanced | |
| Dynamic weights (configurable) | Admin-adjustable weights — more complex | |

**Auto-selected:** Weighted factors with defined ranges (recommended)
**Notes:** Condition score from wear_percentage + technical_condition text mapping + last inspection. Consequence from structure type, suspended area, structure count. Seasonal from Kazakhstan flood season (March-May). Staleness from days since last inspection.

| Option | Description | Selected |
|--------|-------------|----------|
| Threshold bands with emergency override | Score ≥200→emergency, 150-199→30d, 100-149→90d, 60-99→180d, 30-59→12mo, <30→24mo | ✓ |
| Continuous mapping (linear interpolation) | Smoother but less legible | |
| Percentile-based | Relative to portfolio — not absolute | |

**Auto-selected:** Threshold bands with emergency override (recommended)
**Notes:** Matches RISK-02's five intervals + emergency override. Legible and defensible.

| Option | Description | Selected |
|--------|-------------|----------|
| Persist in risk_assessments table with history | Enables trend analysis, audit trail, fast API responses | ✓ |
| Compute on-demand only | Always fresh but slower, no history | |
| Cache in Redis only | Fast but no persistent history | |

**Auto-selected:** Persist in risk_assessments table with history (recommended)
**Notes:** Table stores all factors, composite score, interval, repair status, red flags, contributing factors, provenance. Latest has valid_to=NULL.

| Option | Description | Selected |
|--------|-------------|----------|
| Event-driven + scheduled daily refresh | After inspection/structure update + Celery Beat daily | ✓ |
| Real-time (compute on every request) | Always fresh but expensive | |
| Manual only (engineer triggers) | Simple but stale | |

**Auto-selected:** Event-driven + scheduled daily refresh (recommended)
**Notes:** Risk is a snapshot, not a live calculation. Daily refresh handles seasonal modifier changes.

---

## Repair Status Determination

| Option | Description | Selected |
|--------|-------------|----------|
| Weighted blend: wear 40% + condition text 40% + inspection 20% | Uses available data, weights most reliable sources higher | ✓ |
| Equal weights (33% each) | Simpler but less accurate | |
| ML-based classification | More sophisticated but black-box | |

**Auto-selected:** Weighted blend (recommended)
**Notes:** Score 0 = perfect, 100 = total failure. technical_condition text mapping: хорошее→90, удовлетворительное→60, неудовлетворительное→30, аварийное→10.

| Option | Description | Selected |
|--------|-------------|----------|
| Seepage, deformation, rapid erosion, repeated emergencies, wear≥80%, аварийное condition | Matches RISK-03 specification | ✓ |
| Only structural indicators (seepage, deformation) | Narrower set | |
| Include all inspection findings | Too broad, false positives | |

**Auto-selected:** Full red-flag set from RISK-03 (recommended)
**Notes:** Red flags from inspection findings (text matching) or structure_facts. Stored as JSONB array in risk_assessments.

| Option | Description | Selected |
|--------|-------------|----------|
| Threshold bands: 0-39 normal, 40-69 inspection, 70-89 repair, 90-100 critical | Clear, defensible thresholds | ✓ |
| Ternary (normal/repair/critical) | Missing "inspection required" middle ground | |
| Continuous risk gradient | Less actionable | |

**Auto-selected:** Four-band threshold mapping (recommended)
**Notes:** Matches RISK-04's four statuses. Red flags override to critical regardless of score.

| Option | Description | Selected |
|--------|-------------|----------|
| Floor status at 'inspection required' when evidence is weak/stale/conflicting | Matches RISK-05, prevents false certainty | ✓ |
| Ignore evidence quality | Simpler but unsafe | |
| Separate "uncertain" status | Adds complexity beyond four statuses | |

**Auto-selected:** Floor at "inspection required" for weak evidence (recommended)
**Notes:** Triggers: LOW confidence, no inspection ever, >24mo since last inspection, conflicting facts.

---

## RBAC Implementation

| Option | Description | Selected |
|--------|-------------|----------|
| JWT with role claims | Stateless, PWA-compatible, standard for FastAPI | ✓ |
| Session-based (server-side sessions) | More control but stateful | |
| API key with role lookup | Simpler but less standard | |

**Auto-selected:** JWT with role claims (recommended)
**Notes:** Users table with role enum. JWT contains user_id, username, role, expiry.

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal: token issuance + role enforcement dependencies | Enough for RBAC, not a full auth system | ✓ |
| Full auth (registration, password reset, OAuth) | Complete but out of scope | |
| No auth (header-based role passing) | Too insecure | |

**Auto-selected:** Minimal auth flow (recommended)
**Notes:** POST /auth/token for JWT issuance, GET /auth/me for user info, FastAPI dependencies for role enforcement.

| Option | Description | Selected |
|--------|-------------|----------|
| Matrix: viewer=read, inspector=+inspect/upload, engineer=+edit/override, admin=+delete/manage | Clear hierarchy, matches RISK-07 | ✓ |
| Flat permissions (all or nothing) | Too coarse | |
| ABAC (attribute-based) | More flexible but overkill | |

**Auto-selected:** Hierarchical role permission matrix (recommended)
**Notes:** Four roles with escalating capabilities. All roles can view and export.

| Option | Description | Selected |
|--------|-------------|----------|
| Override endpoint creates provenance + flagged risk_assessment record | Full audit trail, matches RISK-06 | ✓ |
| Direct update of structure fields | No audit trail | |
| Separate override table | More normalized but more complex | |

**Auto-selected:** Override endpoint with provenance + flagged record (recommended)
**Notes:** POST /structures/{id}/override. Creates provenance (source_type="manual", contributor=engineer). System values preserved alongside override. Override expires on new inspection.

---

## Inspection History & Document Attachments

| Option | Description | Selected |
|--------|-------------|----------|
| One row per inspection with findings, condition, red_flags as JSONB | Normalized, queryable, supports DATA-05 | ✓ |
| Inspections as structure_facts | Reuses existing pattern but harder to query | |
| Separate findings table (normalized) | More normalized but more joins | |

**Auto-selected:** Dedicated inspections table (recommended)
**Notes:** Fields: id, structure_id, inspection_date, inspector_name, inspector_role, findings, condition_at_inspection, condition_score_at_inspection, red_flags_observed (JSONB), provenance_id, created_at.

| Option | Description | Selected |
|--------|-------------|----------|
| Separate inspection_photos table with MinIO object keys | Clean separation, supports multiple photos | ✓ |
| Photos as JSONB array on inspection record | Simpler but less queryable | |
| Photos as documents (reuse documents table) | Conflates two concepts | |

**Auto-selected:** Separate inspection_photos table (recommended)
**Notes:** Fields: id, inspection_id, minio_bucket, minio_object_key, caption, photo_type (overview/detail/defect), provenance_id, created_at. Binary in MinIO sujoly-photos bucket.

| Option | Description | Selected |
|--------|-------------|----------|
| Create + list + detail, photo upload via presigned URL flow | Matches DATA-05, reuses MinIO pattern | ✓ |
| Full CRUD (including update/delete inspections) | More complete but inspections are immutable records | |
| Only create + list | Missing detail view | |

**Auto-selected:** Create + list + detail endpoints (recommended)
**Notes:** Photo flow: client gets presigned URL → uploads to MinIO → includes object key in create request. Creating inspection triggers risk recomputation.

| Option | Description | Selected |
|--------|-------------|----------|
| Documents table with MinIO object keys, type enum, language field | Supports DATA-06, trilingual metadata | ✓ |
| Documents as structure_facts | Reuses pattern but wrong semantics | |
| File system storage | Violates INT-04 architecture separation | |

**Auto-selected:** Documents table with MinIO integration (recommended)
**Notes:** Fields: id, structure_id (nullable), document_type (passport/inspection_report/technical_spec/photo/other), title, language (ru/kk/en), minio_bucket, minio_object_key, file_size_bytes, uploaded_by, provenance_id, created_at.

| Option | Description | Selected |
|--------|-------------|----------|
| Register + list + delete + download, upload via presigned URL | Matches DATA-06, reuses existing MinIO pattern | ✓ |
| Only upload + download | Missing list and management | |
| Direct file upload through API | Slower, more API load | |

**Auto-selected:** Full document management endpoints (recommended)
**Notes:** Upload flow: client gets presigned URL → uploads to MinIO → registers metadata via API. Download via presigned URL.

---

## Export Endpoints

| Option | Description | Selected |
|--------|-------------|----------|
| Three endpoints: structures CSV, structures GeoJSON, inspection report PDF — all with lang param | Matches RISK-08 | ✓ |
| Single endpoint with format parameter | Less explicit | |
| Separate endpoints per language | Too many endpoints | |

**Auto-selected:** Three export endpoints with lang parameter (recommended)
**Notes:** /export/structures?format=csv|geojson&lang=ru|kk|en, /export/inspection-report/{id}?lang=ru|kk|en. Filters as query params.

| Option | Description | Selected |
|--------|-------------|----------|
| StreamingResponse with csv module, UTF-8 BOM for Excel | Memory-efficient, Excel-compatible | ✓ |
| Pandas to_csv | Heavy dependency for simple CSV | |
| In-memory string buffer | Not streaming, memory issues for large datasets | |

**Auto-selected:** StreamingResponse with csv module (recommended)
**Notes:** UTF-8 with BOM for Excel Cyrillic compatibility. Columns include all structure fields + risk assessment.

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse existing GeoJSON format + risk fields in properties | Consistent with Phase 2 pattern | ✓ |
| Custom GeoJSON schema | Diverges from existing API | |
| Shapefile export | Requires GDAL, overkill | |

**Auto-selected:** Reuse existing GeoJSON format (recommended)
**Notes:** Extends Phase 2 D-16 GeoJSON FeatureCollection with risk assessment fields in properties.

| Option | Description | Selected |
|--------|-------------|----------|
| WeasyPrint with Jinja2 templates | HTML/CSS templating, native Cyrillic/Kazakh support, easier to maintain | ✓ |
| ReportLab | Programmatic PDF, more control but harder to style | |
| FPDF | Lightweight but limited Cyrillic support | |

**Auto-selected:** WeasyPrint with Jinja2 templates (recommended)
**Notes:** One template per language. Includes structure identity, inspection details, findings, photos (base64 from MinIO), risk assessment, provenance. Official document formatting.

| Option | Description | Selected |
|--------|-------------|----------|
| Server-side translations dict in exports module | Self-contained, no external i18n dependency | ✓ |
| Use next-intl (frontend i18n) | Wrong layer — that's frontend | |
| Database-stored translations | Overkill for export labels | |

**Auto-selected:** Server-side translations dict (recommended)
**Notes:** Translations for column headers, report sections, status names in ru/kk/en in exports.py.

---

## the agent's Discretion

- Specific weight values within defined ranges (condition score blend, consequence factor calculation)
- Red-flag keyword lists for Russian/Kazakh text matching
- JWT token expiry duration and refresh strategy
- Password/API key storage mechanism for minimal auth
- Pydantic schema field names and response structures
- Alembic migration numbering (from 0003)
- Database index strategy for new tables
- Error handling for risk computation edge cases
- WeasyPrint template HTML/CSS structure
- CSV column ordering and field selection
- Redis caching for risk assessments
- Test fixture data for risk model unit tests
- Celery Beat schedule configuration

## Deferred Ideas

- Full authentication system (registration, password reset, OAuth, MFA)
- Risk model ML enhancement using historical data
- Real-time risk alerts and push notifications
- Risk model calibration UI dashboard
- Bulk export with async Celery job
- Document OCR and text extraction (Phase 4/5)
- Inspection template/forms per structure type
- Risk score versioning and trend comparison API
