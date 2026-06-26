# Phase 3: Risk Models & Inspection Logic - Context

**Gathered:** 2026-06-26
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the risk computation and inspection management layer: a semi-quantitative risk model that computes inspection intervals per structure, a blended condition score with red-flag overrides that assigns repair status, inspection history endpoints with photo attachments via MinIO, document attachment endpoints, role-based access control (RBAC) with four roles and engineer override provenance logging, and trilingual export endpoints (CSV/GeoJSON/PDF).

**In scope:** Risk score computation module (condition × consequence × seasonal × staleness), inspection interval mapping (30d–24mo + emergency override), repair status determination (blended score + red-flag overrides + weak-evidence preference), inspections table and CRUD endpoints, document attachments table and endpoints via MinIO presigned URLs, RBAC with JWT auth (admin/engineer/inspector/viewer), engineer override endpoints with provenance logging, export endpoints (CSV, GeoJSON, PDF) in Russian/Kazakh/English, Alembic migrations for new tables.

**Out of scope:** Full authentication system with registration/password reset/OAuth (only JWT issuance + role enforcement needed for RBAC), OSM/satellite data ingestion (Phase 4), discovery/matching algorithms (Phase 4), RAG agent integration (Phase 5), frontend UI (frontend workstream), real-time IoT sensor integration (out of project scope).

</domain>

<decisions>
## Implementation Decisions

### Risk Score Model Design
- **D-01:** Implement the risk computation as a pure Python module (`apps/api/src/api/services/risk_engine.py`) — not a database function or stored procedure. This ensures testability, explainability, and alignment with the "semi-quantitative, defensible" principle from PROJECT.md. The module takes structure data + facts as input and returns a risk assessment with interval, score breakdown, and contributing factors.
  - [auto] Risk Score Model — Q: "Database function vs Python module for risk computation?" → Selected: "Pure Python module" (recommended — testable, explainable, no DB coupling)

- **D-02:** Risk formula factors per RISK-01 (condition score × consequence factor × seasonal modifier × data staleness modifier):
  - **Condition score (0-100):** Derived from `wear_percentage` (inverted: 100 - wear%), `technical_condition` text mapping (хорошее→90, удовлетворительное→60, неудовлетворительное→30, аварийное→10), and last inspection findings if available. Blended with weights: wear 40%, technical_condition 40%, last inspection 20% (if no inspection, weight redistributes to wear/condition).
  - **Consequence factor (0.5-2.0):** Based on structure type (dam/weir → 2.0, canal → 1.0), `suspended_area` (ha) — larger area = higher consequence, `structure_count` — more dependent structures = higher consequence. Default 1.0 when data missing.
  - **Seasonal modifier (0.8-1.5):** Flood season (March-May in Kazakhstan) → 1.5, pre-flood inspection period (January-February) → 1.2, dry season → 0.8. Computed from current date at assessment time.
  - **Data staleness modifier (0.5-1.5):** Days since last inspection: <90d → 0.5 (fresh data, lower urgency), 90-180d → 0.8, 180-365d → 1.0, 365-730d → 1.2, >730d → 1.5 (stale data, higher urgency). If never inspected → 1.5.
  - [auto] Risk Score Model — Q: "What factors and weight ranges for the risk formula?" → Selected: "Condition 40%/40%/20%, consequence 0.5-2.0, seasonal 0.8-1.5, staleness 0.5-1.5" (recommended — covers RISK-01 factors with defensible ranges)

- **D-03:** Composite risk score = condition_score × consequence_factor × seasonal_modifier × staleness_modifier. Range: 0-300 (100 × 2.0 × 1.5 × 1.5 = 450 max, but typical 0-300). Map to inspection intervals via threshold bands:
  - Score ≥ 200 OR any red-flag → **emergency** (immediate inspection, override)
  - Score 150-199 → **30 days**
  - Score 100-149 → **90 days**
  - Score 60-99 → **180 days**
  - Score 30-59 → **12 months**
  - Score < 30 → **24 months**
  - [auto] Risk Score Model — Q: "How to map composite score to the five intervals + emergency?" → Selected: "Threshold bands with emergency override" (recommended — legible, defensible, matches RISK-02)

- **D-04:** Store computed risk assessments in a `risk_assessments` table: id (UUID PK), structure_id (FK), condition_score (Float), consequence_factor (Float), seasonal_modifier (Float), staleness_modifier (Float), composite_score (Float), inspection_interval (String enum: emergency/30d/90d/180d/12mo/24mo), repair_status (String enum: normal/inspection_required/repair_required/critical_condition), red_flags (JSONB array of triggered flags), contributing_factors (JSONB breakdown), provenance_id (FK), computed_at (timestamptz), valid_to (timestamptz nullable). Latest assessment per structure has valid_to=NULL. Historical assessments retained for trend analysis.
  - [auto] Risk Score Model — Q: "Store risk scores in DB or compute on-demand?" → Selected: "Persist in risk_assessments table with history" (recommended — enables trend analysis, audit trail, fast API responses)

- **D-05:** Risk recomputation triggers: (1) after new inspection is recorded, (2) after structure update, (3) Celery Beat scheduled job (daily) to recompute seasonal modifier changes, (4) manual trigger via API endpoint by engineer/admin. Not real-time — risk is a snapshot, not a live calculation.
  - [auto] Risk Score Model — Q: "When should risk scores be recomputed?" → Selected: "Event-driven + scheduled daily refresh" (recommended — balances freshness with performance)

### Repair Status Determination
- **D-06:** Blended condition score (0-100) for repair status (separate from risk interval score, but shares the condition_score component). Inputs: wear_percentage (40%), technical_condition text (40%), last inspection findings severity (20%). Score 0 = perfect condition, 100 = total failure.
  - [auto] Repair Status — Q: "How to compute the blended condition score?" → Selected: "Weighted blend: wear 40% + condition text 40% + inspection 20%" (recommended — uses available data, weights most reliable sources higher)

- **D-07:** Red-flag overrides (RISK-03) — any of these triggers automatically set repair status to "critical condition" regardless of blended score:
  - Seepage through dam body or foundation (просачивание)
  - Visible deformation (деформация)
  - Rapid erosion (быстрая эрозия)
  - Repeated emergency events (повторные аварийные ситуации)
  - Wear percentage ≥ 80%
  - Technical condition = "аварийное" (emergency condition)
  Red flags are stored as a JSONB array in risk_assessments. Detection: red flags come from inspection findings (text matching against keyword list) or from structure_facts attributes.
  - [auto] Repair Status — Q: "What are the red-flag triggers?" → Selected: "Seepage, deformation, rapid erosion, repeated emergencies, wear≥80%, аварийное condition" (recommended — matches RISK-03 specification)

- **D-08:** Four repair statuses (RISK-04) mapping from blended score:
  - Score 0-39 AND no red flags → **normal**
  - Score 40-69 OR no red flags but weak evidence → **inspection required**
  - Score 70-89 → **repair required**
  - Score 90-100 OR any red flag → **critical condition**
  - [auto] Repair Status — Q: "How to map blended score to four statuses?" → Selected: "Threshold bands: 0-39 normal, 40-69 inspection, 70-89 repair, 90-100 critical" (recommended — clear, defensible thresholds)

- **D-09:** Weak evidence rule (RISK-05) — prefer "inspection required" over false certainty when:
  - Provenance confidence_level = LOW on the structure's current facts
  - No inspection has ever been recorded for the structure
  - Last inspection was >24 months ago
  - Conflicting facts exist (same attribute with different values from different sources)
  When weak evidence is detected, bump status to at least "inspection required" (never downgrade below it). This means a structure with score 25 (would be "normal") gets "inspection required" if its data is stale or low-confidence.
  - [auto] Repair Status — Q: "How to implement the weak-evidence preference?" → Selected: "Floor status at 'inspection required' when evidence is weak/stale/conflicting" (recommended — matches RISK-05, prevents false certainty)

### RBAC Implementation
- **D-10:** JWT-based authentication with role claims. Stateless, works with PWA architecture. A `users` table stores: id (UUID PK), username (String unique), role (String enum: admin/engineer/inspector/viewer), full_name (String), created_at. JWT tokens contain user_id, username, role, and expiry. Token validation via FastAPI dependency.
  - [auto] RBAC — Q: "JWT vs session-based auth?" → Selected: "JWT with role claims" (recommended — stateless, PWA-compatible, standard for FastAPI)

- **D-11:** Minimal auth flow — just enough to support RBAC:
  - `POST /api/v1/auth/token` — accepts username (or API key), returns JWT token. No password hashing in Phase 3 — use a simple shared secret or API key lookup from the users table. This is a demo/MVP system; production auth is a separate concern.
  - `GET /api/v1/auth/me` — returns current user info from token
  - FastAPI `get_current_user` dependency extracts user from JWT
  - FastAPI `require_role(role)` dependency factory for role enforcement
  - [auto] RBAC — Q: "How much auth flow to implement?" → Selected: "Minimal: token issuance + role enforcement dependencies" (recommended — enough for RBAC, not a full auth system)

- **D-12:** Role permissions matrix:
  | Capability | admin | engineer | inspector | viewer |
  |---|---|---|---|---|
  | View structures/inspections | ✓ | ✓ | ✓ | ✓ |
  | Export CSV/GeoJSON/PDF | ✓ | ✓ | ✓ | ✓ |
  | Create inspection record | ✓ | ✓ | ✓ | ✗ |
  | Upload documents/photos | ✓ | ✓ | ✓ | ✗ |
  | Create/update structure | ✓ | ✓ | ✗ | ✗ |
  | Override risk interval/status | ✓ | ✓ | ✗ | ✗ |
  | Delete structure | ✓ | ✗ | ✗ | ✗ |
  | Manage users | ✓ | ✗ | ✗ | ✗ |
  - [auto] RBAC — Q: "What permissions per role?" → Selected: "Matrix: viewer=read, inspector=+inspect/upload, engineer=+edit/override, admin=+delete/manage" (recommended — clear hierarchy, matches RISK-07)

- **D-13:** Engineer override (RISK-06) — `POST /api/v1/structures/{id}/override` endpoint. Engineer or admin sets a manual inspection_interval and/or repair_status. Creates a new provenance record with source_type="manual", contributor=engineer username, confidence_level="HIGH" (human decision). The override is stored in risk_assessments with a flag `is_override=true`. The system-computed values are preserved in the same record for audit. Overrides expire when a new inspection is recorded (which triggers recomputation).
  - [auto] RBAC — Q: "How to implement engineer override with provenance?" → Selected: "Override endpoint creates provenance + flagged risk_assessment record" (recommended — full audit trail, matches RISK-06)

### Inspection History & Document Attachments
- **D-14:** `inspections` table (DATA-05): id (UUID PK), structure_id (FK to structures), inspection_date (Date), inspector_name (String), inspector_role (String), findings (Text), condition_at_inspection (String), condition_score_at_inspection (Float nullable), red_flags_observed (JSONB array), provenance_id (FK), created_at (timestamptz). One row per inspection event. Photos are linked via a separate `inspection_photos` table.
  - [auto] Inspection History — Q: "How to structure the inspections table?" → Selected: "One row per inspection with findings, condition, red_flags as JSONB" (recommended — normalized, queryable, supports DATA-05)

- **D-15:** `inspection_photos` table: id (UUID PK), inspection_id (FK), minio_bucket (String), minio_object_key (String), caption (Text nullable), photo_type (String: overview/detail/defect), provenance_id (FK), created_at. Photos are uploaded to MinIO `sujoly-photos` bucket. The API stores only the object key + metadata; the binary lives in MinIO (INT-04 architecture separation).
  - [auto] Inspection History — Q: "How to handle inspection photos?" → Selected: "Separate inspection_photos table with MinIO object keys" (recommended — clean separation, supports multiple photos per inspection)

- **D-16:** Inspection endpoints:
  - `POST /api/v1/structures/{id}/inspections` — create inspection (inspector+ roles). Accepts findings, condition, photos metadata. For each photo: client first gets presigned upload URL from `/api/v1/minio/presign`, uploads to MinIO, then includes the object key in the inspection create request.
  - `GET /api/v1/structures/{id}/inspections` — list inspections for a structure (all roles). Returns inspections with photo presigned download URLs.
  - `GET /api/v1/structures/{id}/inspections/{inspection_id}` — get single inspection detail with photos.
  - Creating an inspection triggers risk recomputation for that structure.
  - [auto] Inspection History — Q: "What endpoints for inspection CRUD?" → Selected: "Create + list + detail, photo upload via presigned URL flow" (recommended — matches DATA-05, reuses MinIO pattern)

- **D-17:** `documents` table (DATA-06): id (UUID PK), structure_id (FK nullable — some documents may not be structure-specific), document_type (String enum: passport/inspection_report/technical_spec/photo/other), title (String), language (String: ru/kk/en), minio_bucket (String), minio_object_key (String), file_size_bytes (Integer nullable), uploaded_by (String), provenance_id (FK), created_at. Documents are stored in MinIO `sujoly-documents` bucket.
  - [auto] Document Attachments — Q: "How to structure document attachments?" → Selected: "Documents table with MinIO object keys, type enum, language field" (recommended — supports DATA-06, trilingual metadata)

- **D-18:** Document endpoints:
  - `POST /api/v1/structures/{id}/documents` — register a document (inspector+ roles). Client uploads to MinIO first via presigned URL, then registers metadata. Returns document record.
  - `GET /api/v1/structures/{id}/documents` — list documents for a structure (all roles). Returns metadata with presigned download URLs.
  - `DELETE /api/v1/documents/{id}` — delete document record + MinIO object (admin only).
  - `GET /api/v1/documents/{id}/download` — generate presigned download URL for a specific document.
  - [auto] Document Attachments — Q: "What endpoints for document management?" → Selected: "Register + list + delete + download, upload via presigned URL" (recommended — matches DATA-06, reuses existing MinIO pattern)

### Export Endpoints
- **D-19:** Export endpoints at `/api/v1/export`:
  - `GET /api/v1/export/structures?format=csv&lang=ru` — export structure list as CSV
  - `GET /api/v1/export/structures?format=geojson&lang=ru` — export as GeoJSON FeatureCollection
  - `GET /api/v1/export/inspection-report/{inspection_id}?lang=ru` — generate PDF inspection report
  - All endpoints accept `lang` parameter (ru/kk/en) for trilingual output (RISK-08).
  - Filters passed as query params (type, district, condition, bbox) to scope the export.
  - [auto] Export — Q: "What export endpoints and parameters?" → Selected: "Three endpoints: structures CSV, structures GeoJSON, inspection report PDF — all with lang param" (recommended — matches RISK-08)

- **D-20:** CSV export: streaming response using Python's `csv` module with `StreamingResponse`. Columns include all structure fields + current risk assessment (interval, status, score). Headers in the selected language. UTF-8 with BOM for Excel compatibility with Cyrillic text.
  - [auto] Export — Q: "How to implement CSV export?" → Selected: "StreamingResponse with csv module, UTF-8 BOM for Excel" (recommended — memory-efficient, Excel-compatible)

- **D-21:** GeoJSON export: reuse the existing GeoJSON FeatureCollection format from the structures list endpoint (Phase 2 D-16). Add risk assessment fields to properties. Streaming for large datasets.
  - [auto] Export — Q: "How to implement GeoJSON export?" → Selected: "Reuse existing GeoJSON format + risk fields in properties" (recommended — consistent with Phase 2 pattern)

- **D-22:** PDF export: use WeasyPrint (HTML→PDF) with Jinja2 templates. One template per language (ru/kk/en) with localized labels. Template includes: structure identity, inspection details, findings, photos (embedded as base64 from MinIO), risk assessment summary, provenance summary. WeasyPrint handles Cyrillic and Kazakh scripts natively. Add `weasyprint` and `jinja2` to dependencies.
  - [auto] Export — Q: "WeasyPrint vs ReportLab for PDF generation?" → Selected: "WeasyPrint with Jinja2 templates" (recommended — HTML/CSS templating, native Cyrillic/Kazakh support, easier to maintain)

- **D-23:** Trilingual export labels: maintain a translations dict in `apps/api/src/api/services/exports.py` with keys for all column headers, report sections, and status names in ru/kk/en. Not using next-intl (that's frontend) — this is server-side translation for export documents only.
  - [auto] Export — Q: "How to handle trilingual labels in exports?" → Selected: "Server-side translations dict in exports module" (recommended — self-contained, no external i18n dependency for backend)

### the agent's Discretion
- Specific weight values within the defined ranges (condition score blend weights, consequence factor calculation details)
- Exact keyword lists for red-flag text matching (Russian/Kazakh inspection finding keywords)
- JWT token expiry duration and refresh strategy
- Password/API key storage mechanism for the minimal auth flow
- Pydantic schema field names and response structure details for new endpoints
- Alembic migration numbering (continue from 0002)
- Database index strategy for new tables (which columns get B-tree vs GIN vs GiST)
- Error handling and validation specifics for risk computation edge cases
- WeasyPrint template HTML/CSS structure and styling
- CSV column ordering and which fields to include/exclude
- Whether to add a `risk_assessments` cache in Redis for frequently-accessed structures
- Test fixture data for risk model unit tests
- Celery Beat schedule configuration for daily risk recomputation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning & Requirements
- `.planning/workstreams/backend/ROADMAP.md` — Phase 3 goal, success criteria, requirements (DATA-05, DATA-06, RISK-01 through RISK-08)
- `.planning/workstreams/backend/REQUIREMENTS.md` — Full requirement definitions with traceability. RISK-01..08 and DATA-05..06 are the Phase 3 requirements.
- `.planning/workstreams/backend/phases/01-foundation-infrastructure/01-CONTEXT.md` — Phase 1 decisions (infrastructure, provenance model, MinIO buckets, patterns to follow)
- `.planning/workstreams/backend/phases/02-data-ingestion-spatial-api/02-CONTEXT.md` — Phase 2 decisions (REST API patterns, service layer, schema additions, search implementation)

### Technology Stack & Architecture
- `AGENTS.md` (STACK.md section) — Verified versions: FastAPI 0.128, SQLAlchemy 2.0, Celery 5.4, Pydantic 2.x. Architecture principle: "LLMs never make final engineering decisions."
- `.planning/PROJECT.md` — Key decisions: "Semi-quantitative risk index over black-box ML" (defensible, explainable, aligns with international dam safety practice), "Condition score + red-flag overrides" (safer than pure scoring, avoids false certainty). Architecture principle: "Every structure has one canonical asset record, many evidence sources, and a time-based condition history."

### Existing Code Patterns to Follow
- `apps/api/src/api/routes/structures.py` — Route pattern: APIRouter prefix=/api/v1, Pydantic models, query params, pagination, GeoJSON format option
- `apps/api/src/api/routes/minio.py` — MinIO presigned URL endpoint pattern (reuse for document/inspection photo uploads)
- `apps/api/src/api/services/structure_service.py` — Service layer pattern: async_session, session.begin(), structlog, select with optional filters
- `apps/api/src/api/services/minio_client.py` — MinIOService class: ensure_bucket, presigned_upload_url, presigned_download_url. Buckets: sujoly-imagery, sujoly-documents, sujoly-photos
- `apps/api/src/api/models/structure.py` — StructureModel + StructureFactModel ORM definitions (the schema Phase 3 builds on)
- `apps/api/src/api/models/provenance.py` — ProvenanceModel ORM: id, source_type, source_reference, confidence_level (HIGH/MEDIUM/LOW), contributor, recorded_at
- `apps/api/src/api/config/settings.py` — Settings pattern (API_ prefix, env loading). NO auth settings yet — need to add JWT secret, token expiry
- `apps/api/src/api/main.py` — App setup: lifespan, CORS, middleware, router registration. New routers (inspections, documents, auth, exports, risk) registered here
- `apps/api/alembic/versions/0001_initial.py` — Migration pattern: op.create_table, Geometry columns, GiST indexes, CheckConstraint
- `apps/api/alembic/versions/0002_add_filterable_columns_and_search.py` — Migration pattern for schema additions
- `apps/api/src/api/infrastructure/database.py` — Async engine, async_session factory, get_session dependency, Base declarative
- `apps/api/pyproject.toml` — Dependencies already installed (fastapi, sqlalchemy, geoalchemy2, asyncpg, alembic, celery, pgvector, psycopg). Need to add: weasyprint, jinja2, PyJWT (or python-jose)

### Infrastructure
- `docker-compose.yml` — Current service stack (postgres, redis, minio, api, celery-worker). No changes needed for Phase 3.
- `.env.example` — Environment variable template. JWT secret and token expiry need to be added.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/api/src/api/routes/minio.py` — Presigned URL endpoints (POST /presign, GET /presign/{object_name}). Reuse directly for document and inspection photo uploads. Client flow: get presigned URL → upload to MinIO → register metadata via API.
- `apps/api/src/api/services/minio_client.py` — MinIOService with ensure_bucket, presigned_upload_url (1hr), presigned_download_url (2hr). Already initialized in lifespan. Buckets sujoly-photos and sujoly-documents already created.
- `apps/api/src/api/routes/structures.py` — Complete CRUD route pattern to mirror for inspections, documents, risk endpoints. Includes GeoJSON format option (reuse for GeoJSON export).
- `apps/api/src/api/services/structure_service.py` — Service layer pattern: async_session, session.begin(), structlog, select with optional where clauses. Mirror for new services.
- `apps/api/src/api/models/structure.py` — StructureModel with filterable columns (district, water_source, technical_condition, wear_percentage, commissioning_year, structure_count) — these feed the risk computation. StructureFactModel for detailed attributes.
- `apps/api/src/api/models/provenance.py` — ProvenanceModel for logging engineer overrides and inspection provenance. source_type can be "manual" for overrides, "inspection" for inspection records.
- `apps/api/src/api/tasks/celery_tasks.py` — Celery app stubs ready for risk recomputation task.
- `apps/api/src/api/celery_app.py` — Celery app configuration for Beat scheduling.

### Established Patterns
- **Routes:** APIRouter with prefix="/api/v1", Pydantic Create/Response models with ConfigDict(from_attributes=True), HTTPException for 404
- **Services:** async with async_session() as session → async with session.begin() → add/flush/refresh for creates; select() with optional .where() for queries
- **Models:** SQLAlchemy 2.0 Mapped types, UUID primary keys, DateTime(timezone=True), JSONB for flexible data
- **Migrations:** Alembic with op.create_table, op.create_index, op.execute for raw SQL. Continue numbering from 0003.
- **Config:** Pydantic Settings with env_prefix="API_", .env loading via python-dotenv
- **MinIO:** Presigned URL pattern for upload/download. Binary assets never in PostgreSQL.
- **Provenance:** Every fact/status has provenance_id FK. ProvenanceModel records source_type, confidence_level, contributor.
- **No auth exists** — CORS allows Authorization header but no auth dependency is implemented. Phase 3 adds JWT auth + role dependencies.

### Integration Points
- `apps/api/src/api/main.py` — New routers registered via `app.include_router()`: auth, inspections, documents, risk, exports
- `apps/api/src/api/config/settings.py` — Add JWT secret key, token expiry, initial admin credentials
- `apps/api/src/api/tasks/celery_tasks.py` — Risk recomputation Celery task added here
- `apps/api/alembic/versions/` — New migrations (0003+) for: users, inspections, inspection_photos, documents, risk_assessments tables
- `apps/api/src/api/models/` — New model files: user.py, inspection.py, document.py, risk_assessment.py
- `apps/api/src/api/services/` — New service files: risk_engine.py, auth_service.py, inspection_service.py, document_service.py, export_service.py
- `apps/api/src/api/routes/` — New route files: auth.py, inspections.py, documents.py, risk.py, exports.py
- `apps/api/src/api/schemas/` — New schema files for each domain
- `apps/api/pyproject.toml` — Add: weasyprint, jinja2, PyJWT (or python-jose), passlib (if password hashing needed)
- `.env.example` — Add: API_JWT_SECRET, API_JWT_EXPIRY_HOURS, API_INITIAL_ADMIN_USERNAME

</code_context>

<specifics>
## Specific Ideas

- The risk model should be explainable: when an API consumer requests a structure's risk assessment, the response includes the full factor breakdown (condition_score, consequence_factor, seasonal_modifier, staleness_modifier, composite_score, which red_flags triggered, which weak-evidence rules applied). This aligns with the "defensible, explainable" principle and supports the AI copilot's risk explanation tool (Phase 5).
- The seasonal modifier should account for Kazakhstan's flood season: spring floods (March-May) are the critical period for hydraulic structures in Zhambyl Oblast. Pre-flood inspections (January-February) are standard practice. The modifier increases urgency during these periods.
- Red-flag keywords should be in Russian (the primary data language): "просачивание" (seepage), "деформация" (deformation), "эрозия" (erosion), "аварийная ситуация" (emergency situation). The text matching against inspection findings should be case-insensitive and handle morphological variations.
- The PDF inspection report should look official: header with Kazakhstan government formatting conventions, structure identity section, inspection details, findings with photos, risk assessment summary, signatures section. This is a document that could be printed for regulatory purposes.
- Engineer overrides should be clearly visible in the API response: the system-computed values and the override values are both returned, with the override marked as such. This transparency is critical for audit purposes.
- The users table should support an initial admin user created via environment variables or a seed script, so the system is usable immediately after deployment without a registration flow.

</specifics>

<deferred>
## Deferred Ideas

- **Full authentication system** — Registration, password reset, OAuth/social login, MFA, email verification. Phase 3 implements minimal JWT auth for RBAC enforcement only. Full auth is a separate concern.
- **Risk model ML enhancement** — Using historical inspection data to train a predictive model for risk scores. The semi-quantitative model is the MVP; ML enhancement is a future phase.
- **Real-time risk alerts** — Push notifications when a structure's risk score crosses a threshold. Defer to a future notifications phase.
- **Risk model calibration UI** — A dashboard for administrators to adjust factor weights and thresholds. Defer to frontend workstream or a future admin phase.
- **Bulk export with async job** — For very large datasets, a Celery-based async export that generates a file and notifies when ready. Current streaming approach handles the ~444 structure dataset fine.
- **Document OCR and text extraction** — Extracting text from uploaded scanned documents for searchability. Belongs in Phase 4 (OCR pipeline) or Phase 5 (RAG).
- **Inspection template/forms** — Predefined inspection forms per structure type with structured fields. Defer to a future inspection workflow enhancement phase.
- **Risk score versioning and comparison** — Comparing risk scores over time to show trends. The risk_assessments table supports this, but the comparison API and visualization are future work.

</deferred>

---

*Phase: 03-risk-models-inspection-logic*
*Context gathered: 2026-06-26*
