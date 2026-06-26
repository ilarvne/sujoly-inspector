---
phase: 03-risk-models-inspection-logic
reviewed: 2026-06-26T17:45:00Z
depth: deep
files_reviewed: 46
files_reviewed_list:
  - apps/api/src/api/services/risk_engine.py
  - apps/api/tests/test_risk_engine.py
  - apps/api/pyproject.toml
  - apps/api/src/api/config/settings.py
  - apps/api/src/api/main.py
  - apps/api/src/api/models/__init__.py
  - apps/api/src/api/models/user.py
  - apps/api/src/api/services/auth_service.py
  - apps/api/src/api/dependencies/auth.py
  - apps/api/src/api/schemas/auth.py
  - apps/api/src/api/routes/auth.py
  - apps/api/src/api/routes/structures.py
  - apps/api/alembic/versions/0003_users.py
  - apps/api/tests/conftest.py
  - apps/api/tests/test_auth.py
  - apps/api/tests/test_structures.py
  - .env.example
  - docker-compose.yml
  - apps/api/alembic/versions/0004_risk_assessments.py
  - apps/api/src/api/models/risk_assessment.py
  - apps/api/src/api/services/risk_service.py
  - apps/api/src/api/routes/risk.py
  - apps/api/src/api/schemas/risk.py
  - apps/api/src/api/tasks/celery_tasks.py
  - apps/api/src/api/celery_app.py
  - apps/api/tests/test_risk_api.py
  - apps/api/alembic/versions/0005_documents.py
  - apps/api/src/api/models/document.py
  - apps/api/src/api/services/document_service.py
  - apps/api/src/api/routes/documents.py
  - apps/api/src/api/schemas/documents.py
  - apps/api/tests/test_documents.py
  - apps/api/alembic/versions/0006_inspections.py
  - apps/api/src/api/models/inspection.py
  - apps/api/src/api/services/inspection_service.py
  - apps/api/src/api/routes/inspections.py
  - apps/api/src/api/schemas/inspections.py
  - apps/api/tests/test_inspections.py
  - apps/api/Dockerfile
  - apps/api/src/api/services/export_service.py
  - apps/api/src/api/routes/exports.py
  - apps/api/src/api/schemas/exports.py
  - apps/api/templates/inspection_report_ru.html
  - apps/api/templates/inspection_report_kk.html
  - apps/api/templates/inspection_report_en.html
  - apps/api/tests/test_exports.py
findings:
  critical: 6
  warning: 12
  info: 0
  total: 18
status: blocked
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-26T17:45:00Z
**Depth:** deep
**Files Reviewed:** 46
**Status:** blocked

## Summary

Reviewed all Phase 3 source changes for the backend workstream: risk engine, JWT/RBAC, risk assessment persistence with override/recompute, document attachments, inspection history, and trilingual CSV/GeoJSON/PDF exports. All 107 targeted unit tests pass, but adversarial cross-file analysis found several critical security and correctness gaps that must be fixed before the code can ship. The most severe issues are unauthenticated read paths, username-only token issuance, hardcoded/default secrets, missing PDF templates in the Docker runtime image, and the risk engine's weak-evidence floor not receiving provenance confidence from the production recomputation path.

## Critical Issues

### CR-01: Public read endpoints bypass authentication

**File:** `apps/api/src/api/routes/structures.py:39-99,102-151,154-166` and `apps/api/src/api/routes/risk.py:30-50`
**Issue:** `GET /api/v1/structures`, `GET /api/v1/structures/search`, `GET /api/v1/structures/{id}`, and `GET /api/v1/structures/{id}/risk` do not declare any auth dependency. The Phase 3 RBAC matrix and the risk route docstring state these should be accessible to "any authenticated user" / "viewer+", but the implementation leaves them fully public. Any unauthenticated caller can enumerate structures, their risk scores, and inspection intervals.
**Fix:** Inject `current_user: UserModel = Depends(require_role("viewer"))` into each read endpoint, or remove the public read if that was intentional and update the requirements.
```python
from api.dependencies.auth import require_role
from api.models.user import UserModel

@router.get("/structures", response_model=None)
async def list_structures_endpoint(
    ...,
    current_user: UserModel = Depends(require_role("viewer")),
):
    ...
```

### CR-02: Username-only token issuance allows authentication by username alone

**File:** `apps/api/src/api/routes/auth.py:18-46`, `apps/api/src/api/models/user.py:12-31`, `apps/api/src/api/services/auth_service.py:33-39`
**Issue:** `POST /api/v1/auth/token` accepts a `username` and returns a JWT if the username exists, with no password, PIN, or other secret verification. Knowing or guessing a username (e.g., `admin`, `engineer`, `inspector`) is sufficient to authenticate. The `UserModel` has no `password_hash` field.
**Fix:** Add a `password_hash` column to `UserModel`, require a `password` field in `TokenRequest`, and verify it (e.g., with `passlib`/`bcrypt`) before issuing a token. Alternatively, remove the username-only path and require the API key, which is at least a secret.
```python
# Verify password before token issuance
if not verify_password(body.password, user.password_hash):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

### CR-03: Hardcoded/default JWT secret and admin API key in Docker stack

**File:** `apps/api/src/api/config/settings.py:50-53`, `docker-compose.yml:75,78`, `.env.example:20,23`
**Issue:** `Settings.jwt_secret` defaults to an empty string, and `docker-compose.yml` falls back to `dev-secret-change-me` and `dev-admin-key` for `API_JWT_SECRET` and `API_INITIAL_ADMIN_API_KEY`. If the environment variables are not explicitly overridden, the JWT signing key is a public, hardcoded value, allowing trivial token forgery and admin API key impersonation.
**Fix:** Make the application fail closed when secrets are absent or weak. Remove the fallback defaults in `docker-compose.yml` and add startup validation in `settings.py` or `main.py`:
```python
@field_validator("jwt_secret")
@classmethod
def _jwt_secret_must_be_set(cls, v: str) -> str:
    if not v or len(v) < 32:
        raise ValueError("API_JWT_SECRET must be set and >= 32 characters")
    return v
```

### CR-04: Docker runtime image is missing the PDF templates

**File:** `apps/api/Dockerfile:34-35`
**Issue:** The builder stage copies `templates/` into `/app/templates`, but the runtime stage only copies `/app/.venv` and `/app/src`. `export_service.py` resolves templates to `/app/templates/inspection_report_{lang}.html`, so the PDF export endpoint will raise `TemplateNotFound` in any container built from this Dockerfile.
**Fix:** Add the templates to the runtime image:
```dockerfile
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/templates /app/templates
```

### CR-05: Weak-evidence floor is never triggered for low-confidence provenance in production recomputation

**File:** `apps/api/src/api/services/risk_service.py:295-307`, `apps/api/src/api/services/risk_engine.py:326-337`
**Issue:** The risk engine floors `repair_status` to `inspection_required` when `structure.provenance_confidence == "LOW"`. However, `recompute_risk_for_structure` always builds `structure_dict = {"provenance_confidence": None, ...}` regardless of the actual provenance confidence. Therefore, low-confidence source data never triggers the floor in the production recomputation path, violating the D-09 requirement.
**Fix:** Load the structure's `ProvenanceModel` and pass its real `confidence_level`:
```python
provenance_result = await session.execute(
    select(ProvenanceModel).where(ProvenanceModel.id == structure.provenance_id)
)
provenance = provenance_result.scalar_one_or_none()
structure_dict = {
    "type": structure.type,
    "wear_percentage": structure.wear_percentage,
    "technical_condition": structure.technical_condition,
    "provenance_confidence": provenance.confidence_level if provenance else None,
}
```

### CR-06: API keys are stored and compared in plaintext

**File:** `apps/api/src/api/models/user.py:29`, `apps/api/src/api/services/auth_service.py:51-57`, `apps/api/src/api/main.py:56-59`
**Issue:** `api_key` is stored as a plain `String` column, and `get_user_by_api_key` compares the raw submitted key against the database value. The initial admin key is also seeded in plaintext. This violates basic credential-storage hygiene and leaks credentials if the database is compromised.
**Fix:** Hash API keys at rest. Store an `api_key_hash`, generate the raw key once and show it to the admin only at creation time, and compare using a constant-time hash comparison (e.g., HMAC-SHA256 or bcrypt with a pepper).

## Warnings

### WR-01: Global exception handler strips HTTPException headers

**File:** `apps/api/src/api/main.py:87-106`
**Issue:** The custom `global_exception_handler` catches `HTTPException` and returns a `JSONResponse` without forwarding `exc.headers`. This drops the `WWW-Authenticate: Bearer` header on 401 responses, which breaks OAuth2 clients and HTTP spec compliance.
**Fix:** Preserve the original headers:
```python
if isinstance(exc, HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
        headers=exc.headers,
    )
```

### WR-02: Inspection detail endpoint does not verify the inspection belongs to the requested structure

**File:** `apps/api/src/api/routes/inspections.py:107-142`
**Issue:** `GET /api/v1/structures/{structure_id}/inspections/{inspection_id}` fetches the inspection by `inspection_id` but never checks `inspection.structure_id == structure_id`. An authenticated viewer can retrieve any inspection by substituting arbitrary `structure_id` and `inspection_id` values, leading to cross-structure information disclosure.
**Fix:** Validate ownership before returning:
```python
if str(model.structure_id) != str(structure_id):
    raise HTTPException(status_code=404, detail="Inspection not found")
```

### WR-03: GeoJSON export passes raw PostGIS geometry objects without serializing them

**File:** `apps/api/src/api/services/export_service.py:337-346`
**Issue:** `geometry = getattr(struct, "geometry", None)` is placed directly into the GeoJSON feature. With GeoAlchemy2 this is a `WKBElement`, which `JSONResponse` cannot serialize. The export will fail once structures have non-null geometry (Phase 4). The existing structures route works around this by using `StructureResponse.model_validate(...).model_dump()`, which the export service does not.
**Fix:** Reuse the validated response serialization or convert via WKT/GeoJSON:
```python
from shapely import to_geojson
from shapely.geometry import shape as to_shape

geometry = None
if struct.geometry is not None:
    geometry = to_geojson(to_structure(struct.geometry))
```

### WR-04: PDF templates hide zero and other falsy numeric values

**File:** `apps/api/templates/inspection_report_ru.html:90-95,128-134`, `inspection_report_kk.html:90-95,128-134`, `inspection_report_en.html:90-95,128-134`
**Issue:** Numeric fields are rendered as `{{ value or "—" }}`. Jinja2 treats `0`, `0.0`, and empty strings as falsy, so legitimate values like `wear_percentage = 0.0` or `composite_score = 0.0` display as em-dashes instead of the actual number.
**Fix:** Use explicit `none` checks:
```jinja2
{% if structure.wear_percentage is not none %}{{ structure.wear_percentage }}{% else %}—{% endif %}
```

### WR-05: `models/__init__.py` does not import the new Phase 3 models

**File:** `apps/api/src/api/models/__init__.py:7-11`
**Issue:** Only `ProvenanceModel`, `StructureModel`, `StructureFactModel`, and `UserModel` are imported. `RiskAssessmentModel`, `DocumentModel`, `InspectionModel`, and `InspectionPhotoModel` are omitted, so `Base.metadata` does not know about them. Future `alembic revision --autogenerate` runs will generate spurious `create_table` / `drop_table` statements for tables that already exist.
**Fix:** Import and export all models:
```python
from api.models.document import DocumentModel
from api.models.inspection import InspectionModel, InspectionPhotoModel
from api.models.risk_assessment import RiskAssessmentModel

__all__ = [..., "RiskAssessmentModel", "DocumentModel", "InspectionModel", "InspectionPhotoModel"]
```

### WR-06: `RiskAssessmentModel` lacks database-level enum constraints

**File:** `apps/api/src/api/models/risk_assessment.py:42-68`
**Issue:** The Alembic migration adds `ck_risk_interval` and `ck_risk_repair_status` check constraints, but the ORM model does not declare them in `__table_args__`. The model and database schema are out of sync, which can surprise future migrations and unit tests using `Base.metadata`.
**Fix:** Add `__table_args__` mirroring the migration constraints.

### WR-07: Naive `datetime.utcnow()` used for timezone-aware timestamp columns

**File:** `apps/api/src/api/models/user.py:31`, `models/risk_assessment.py:64`, `models/document.py:60`, `models/inspection.py:51,79`, `models/provenance.py:46`, `models/structure.py:55,61`, `services/risk_service.py:87,153`
**Issue:** Columns are declared with `DateTime(timezone=True)`, but the default values are `datetime.utcnow()` which returns a naive datetime. PostgreSQL will interpret the value in the server's local timezone, which can cause subtle timestamp offsets and warning noise from `asyncpg`/`psycopg`.
**Fix:** Use `datetime.now(timezone.utc)` (or `func.now()` at the DB level) for all timezone-aware defaults.

### WR-08: Admin seeding is not protected against concurrent startup races

**File:** `apps/api/src/api/main.py:46-66`
**Issue:** The lifespan check-then-insert pattern is racy. If multiple API containers start concurrently, both may see no admin and attempt to insert the same username, causing an `IntegrityError` that crashes startup.
**Fix:** Catch `IntegrityError` (or use `ON CONFLICT DO NOTHING`) and log a warning instead of crashing.

### WR-09: MinIO `get_object` response is not closed in a context manager

**File:** `apps/api/src/api/services/export_service.py:397-402`
**Issue:** The response from `minio_service.client.get_object()` is read and closed manually, but if an exception occurs between `get_object` and `response.close()`, the HTTP connection is leaked. The `except Exception: logger.warning(...)` swallows the error but still leaks on failure.
**Fix:** Use a context manager:
```python
with minio_service.client.get_object(photo.minio_bucket, photo.minio_object_key) as response:
    photo_bytes = response.read()
```

### WR-10: `sessionmaker` used instead of `async_sessionmaker`

**File:** `apps/api/src/api/infrastructure/database.py:36`
**Issue:** `sessionmaker(engine, class_=AsyncSession, ...)` is technically supported but the SQLAlchemy 2.0 async idiom is `async_sessionmaker`. Using the sync factory can lead to subtle issues with commit/expunge behavior in async code.
**Fix:**
```python
from sqlalchemy.ext.asyncio import async_sessionmaker
async_session = async_sessionmaker(engine, expire_on_commit=False)
```

### WR-11: CSV export always outputs the Russian name column regardless of `lang`

**File:** `apps/api/src/api/services/export_service.py:251`
**Issue:** The CSV row uses `getattr(struct, "name_ru", "")` for all languages, so Kazakh and English exports still show the Russian name. The headers are translated but the name data is not.
**Fix:** Select the name field based on the requested language:
```python
name = getattr(struct, f"name_{lang}", None) or getattr(struct, "name_ru", "") or ""
```

### WR-12: Document registration does not verify the target structure exists

**File:** `apps/api/src/api/routes/documents.py:31-53`, `apps/api/src/api/services/document_service.py:50-84`
**Issue:** The route accepts a `structure_id` and inserts a `DocumentModel` with that FK. If the structure does not exist, the database raises a foreign-key violation and the route returns 500 instead of 404. There is also no guard against a document referencing a soft-deleted structure.
**Fix:** Call `structure_service.get_structure(structure_id)` in the route and return 404 if not found or `status == "deleted"`.

## Info

No info-only findings are reported; all identified issues above affect correctness, security, or maintainability.

---

_Reviewed: 2026-06-26T17:45:00Z_
_Reviewer: gsd-code-reviewer_
_Depth: deep_
