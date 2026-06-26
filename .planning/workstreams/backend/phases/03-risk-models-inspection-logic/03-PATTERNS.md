# Phase 3: Risk Models & Inspection Logic - Pattern Map

**Mapped:** 2026-06-26
**Files analyzed:** 42 (31 new + 11 modified)
**Analogs found:** 36 / 42

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `apps/api/src/api/models/user.py` | model | CRUD | `apps/api/src/api/models/provenance.py` | exact (role+flow) |
| `apps/api/src/api/models/inspection.py` | model | CRUD | `apps/api/src/api/models/structure.py` | exact (role+flow) |
| `apps/api/src/api/models/document.py` | model | CRUD | `apps/api/src/api/models/structure.py` | exact (role+flow) |
| `apps/api/src/api/models/risk_assessment.py` | model | CRUD + event-driven | `apps/api/src/api/models/structure.py` | exact (role+flow) |
| `apps/api/src/api/schemas/auth.py` | schema | request-response | `apps/api/src/api/schemas/structures.py` | exact (role+flow) |
| `apps/api/src/api/schemas/inspections.py` | schema | request-response | `apps/api/src/api/schemas/structures.py` | exact (role+flow) |
| `apps/api/src/api/schemas/documents.py` | schema | request-response | `apps/api/src/api/schemas/structures.py` | exact (role+flow) |
| `apps/api/src/api/schemas/risk.py` | schema | request-response | `apps/api/src/api/schemas/structures.py` | exact (role+flow) |
| `apps/api/src/api/schemas/exports.py` | schema | request-response | `apps/api/src/api/schemas/structures.py` | role-match |
| `apps/api/src/api/services/risk_engine.py` | service (pure Python) | transform | *none in codebase* | no analog |
| `apps/api/src/api/services/auth_service.py` | service | request-response | `apps/api/src/api/services/provenance_service.py` | exact (role+flow) |
| `apps/api/src/api/services/inspection_service.py` | service | CRUD + event-driven | `apps/api/src/api/services/structure_service.py` | exact (role+flow) |
| `apps/api/src/api/services/document_service.py` | service | CRUD + file-I/O | `apps/api/src/api/services/structure_service.py` | role-match |
| `apps/api/src/api/services/export_service.py` | service | streaming + file-I/O | *none in codebase* | no analog |
| `apps/api/src/api/services/risk_service.py` | service | CRUD + event-driven | `apps/api/src/api/services/structure_service.py` | exact (role+flow) |
| `apps/api/src/api/dependencies/auth.py` | middleware | request-response | *none in codebase* | no analog |
| `apps/api/src/api/routes/auth.py` | route | request-response | `apps/api/src/api/routes/provenance.py` | exact (role+flow) |
| `apps/api/src/api/routes/inspections.py` | route | CRUD | `apps/api/src/api/routes/structures.py` | exact (role+flow) |
| `apps/api/src/api/routes/documents.py` | route | CRUD | `apps/api/src/api/routes/structures.py` | exact (role+flow) |
| `apps/api/src/api/routes/risk.py` | route | request-response | `apps/api/src/api/routes/structures.py` | exact (role+flow) |
| `apps/api/src/api/routes/exports.py` | route | streaming + file-I/O | `apps/api/src/api/routes/structures.py` (GeoJSON) | role-match |
| `apps/api/alembic/versions/0003_risk_inspection_document_tables.py` | migration | CRUD | `apps/api/alembic/versions/0001_initial.py` | exact (role+flow) |
| `apps/api/tests/test_risk_engine.py` | test | unit (transform) | `apps/api/tests/test_structures.py` | role-match |
| `apps/api/tests/test_auth.py` | test | unit + integration | `apps/api/tests/test_structures.py` | role-match |
| `apps/api/tests/test_risk_api.py` | test | integration | `apps/api/tests/test_structures.py` | exact (role+flow) |
| `apps/api/tests/test_inspections.py` | test | integration | `apps/api/tests/test_structures.py` | exact (role+flow) |
| `apps/api/tests/test_documents.py` | test | integration | `apps/api/tests/test_structures.py` | exact (role+flow) |
| `apps/api/tests/test_exports.py` | test | integration | `apps/api/tests/test_structures.py` | role-match |
| `apps/api/templates/inspection_report_ru.html` | template | file-I/O | *none in codebase* | no analog |
| `apps/api/templates/inspection_report_kk.html` | template | file-I/O | *none in codebase* | no analog |
| `apps/api/templates/inspection_report_en.html` | template | file-I/O | *none in codebase* | no analog |
| `apps/api/src/api/config/settings.py` *(modify)* | config | request-response | itself | exact |
| `apps/api/src/api/main.py` *(modify)* | config | event-driven | itself | exact |
| `apps/api/src/api/tasks/celery_tasks.py` *(modify)* | task | event-driven | itself | exact |
| `apps/api/src/api/celery_app.py` *(modify)* | config | event-driven | itself | exact |
| `apps/api/pyproject.toml` *(modify)* | config | — | itself | exact |
| `apps/api/Dockerfile` *(modify)* | config | — | itself | exact |
| `docker-compose.yml` *(modify)* | config | — | itself | exact |
| `.env.example` *(modify)* | config | — | itself | exact |
| `apps/api/tests/conftest.py` *(modify)* | test config | — | itself | exact |
| `apps/api/src/api/routes/structures.py` *(modify)* | route | request-response | itself | exact |
| `apps/api/src/api/models/__init__.py` *(modify)* | barrel export | — | itself | exact |

---

## Pattern Assignments

### Model Pattern — applies to `user.py`, `inspection.py`, `document.py`, `risk_assessment.py`

**Analog:** `apps/api/src/api/models/structure.py` (lines 1-89) and `apps/api/src/api/models/provenance.py` (lines 1-47)

**Imports pattern** (`structure.py` lines 12-20):
```python
import uuid
from datetime import datetime

from geoalchemy2 import Geometry  # only if spatial columns needed
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base
```

**Core model pattern** (`structure.py` lines 23-62) — UUID PK, Mapped types, DateTime(timezone=True), JSONB for flexible data, ForeignKey with table name reference:
```python
class StructureModel(Base):
    __tablename__ = "structures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name_ru: Mapped[str | None] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
```

**CheckConstraint pattern** (`provenance.py` lines 28-34) — use for enum-like columns (role, status, type):
```python
class ProvenanceModel(Base):
    __tablename__ = "provenance"
    __table_args__ = (
        CheckConstraint(
            "confidence_level IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_provenance_confidence_level",
        ),
    )
```

**Time-based validity pattern** (`structure.py` lines 84-88) — `valid_to=NULL` means current. Apply to `risk_assessment.py`:
```python
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True  # NULL = currently valid
    )
```

**JSONB pattern** (`structure.py` line 80) — for `red_flags`, `contributing_factors` arrays/dicts:
```python
    attribute_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
```

**Per-file guidance:**

| File | Key differences from analog |
|---|---|
| `user.py` | Follow `provenance.py` (simplest model). Add `CheckConstraint` for role enum (admin/engineer/inspector/viewer). Add `api_key` column (String, nullable, indexed). No `provenance_id` FK — users are not data facts. |
| `inspection.py` | Two models in one file: `InspectionModel` (main) + `InspectionPhotoModel` (child). Follow `StructureFactModel` pattern for the photo child — FK to parent with `index=True`. JSONB for `red_flags_observed`. |
| `document.py` | Follow `StructureModel` pattern. `structure_id` FK nullable (some docs aren't structure-specific). `document_type` with `CheckConstraint` enum. `language` with `CheckConstraint` for ru/kk/en. |
| `risk_assessment.py` | Follow `StructureModel` + `StructureFactModel` hybrid. Add `is_override: Mapped[bool]` (Boolean, default=False). Use `valid_to` pattern for history. JSONB for `red_flags` (list) and `contributing_factors` (dict). See RESEARCH.md lines 901-938 for complete field spec. |

**Barrel export update** (`models/__init__.py` lines 1-10) — add new imports so Alembic discovers them:
```python
from api.models.provenance import ProvenanceModel
from api.models.structure import StructureFactModel, StructureModel
# ADD:
from api.models.user import UserModel
from api.models.inspection import InspectionModel, InspectionPhotoModel
from api.models.document import DocumentModel
from api.models.risk_assessment import RiskAssessmentModel
```

---

### Schema Pattern — applies to `auth.py`, `inspections.py`, `documents.py`, `risk.py`, `exports.py`

**Analog:** `apps/api/src/api/schemas/structures.py` (lines 1-125)

**Imports pattern** (lines 12-15):
```python
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
```

**Create schema pattern** (lines 18-45) — `Field(...)` for required, `Field(None, description="...")` for optional:
```python
class StructureCreate(BaseModel):
    type: str = Field(..., description="Structure type: canal, dam, reservoir, etc.")
    name_ru: str | None = Field(None, description="Structure name in Russian")
    wear_percentage: float | None = Field(None, description="Wear percentage 0-100")
```

**Response schema pattern** (lines 69-94) — `ConfigDict(from_attributes=True)` enables `model_validate()` from ORM models:
```python
class StructureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    name_ru: str | None
    provenance_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
```

**List response envelope pattern** (lines 97-106):
```python
class StructureListResponse(BaseModel):
    items: list[StructureResponse]
    total: int
    offset: int
    limit: int
```

**Update schema pattern** (lines 48-66) — all fields Optional, only non-None updated:
```python
class StructureUpdate(BaseModel):
    name_ru: str | None = None
    type: str | None = None
    # ... all optional
```

**Literal type for enums** (`routes/structures.py` line 44, `routes/provenance.py` line 40):
```python
lang: Literal["ru", "kk", "en"] = "ru"
confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field("HIGH")
```

**Per-file guidance:**

| File | Schemas to create |
|---|---|
| `auth.py` | `TokenRequest` (username/api_key), `TokenResponse` (access_token, token_type), `UserResponse` (id, username, role, full_name, created_at) |
| `inspections.py` | `InspectionCreate`, `PhotoMetadata` (bucket, object_key, caption, photo_type), `InspectionResponse` (with `ConfigDict`), `PhotoResponse`, `InspectionListResponse` |
| `documents.py` | `DocumentCreate` (document_type, title, language, bucket, object_key), `DocumentResponse`, `DocumentListResponse` |
| `risk.py` | `RiskAssessmentResponse` (all factors + breakdown), `OverrideRequest` (inspection_interval, repair_status, reason), `OverrideResponse` (system + override values) |
| `exports.py` | `ExportParams` (format, lang, type, district, condition, bbox) — can be used as query param model |

---

### Route Pattern — applies to `auth.py`, `inspections.py`, `documents.py`, `risk.py`, `exports.py`

**Analog (CRUD routes):** `apps/api/src/api/routes/structures.py` (lines 1-222)
**Analog (simple routes):** `apps/api/src/api/routes/provenance.py` (lines 1-118)

**Imports pattern** (`structures.py` lines 12-32):
```python
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from api.schemas.structures import (
    StructureCreate, StructureResponse, StructureUpdate,
)
from api.services.structure_service import (
    create_structure, get_structure, list_structures, update_structure,
)
```

**Router declaration** (`structures.py` line 34):
```python
router = APIRouter(prefix="/api/v1", tags=["structures"])
```

**GET by ID with 404** (`structures.py` lines 152-164):
```python
@router.get("/structures/{structure_id}", response_model=StructureResponse)
async def get_structure_endpoint(structure_id: uuid.UUID) -> StructureResponse:
    model = await get_structure(structure_id)
    if model is None or model.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Structure '{structure_id}' not found",
        )
    return StructureResponse.model_validate(model)
```

**POST with 201** (`structures.py` lines 167-182):
```python
@router.post(
    "/structures",
    response_model=StructureResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_structure_endpoint(
    body: StructureCreate,
    provenance_id: uuid.UUID = Query(..., description="Provenance UUID"),
) -> StructureResponse:
    model = await create_structure(data=body, provenance_id=provenance_id)
    return StructureResponse.model_validate(model)
```

**List with query params + pagination** (`structures.py` lines 37-97):
```python
@router.get("/structures", response_model=None)
async def list_structures_endpoint(
    type: str | None = None,
    district: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    format: Literal["json", "geojson"] = "json",
):
```

**Inline schema pattern** (`routes/provenance.py` lines 27-58) — for simple schemas, define directly in route file:
```python
class ProvenanceCreate(BaseModel):
    source_type: str = Field(..., description="...")
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field("HIGH")

class ProvenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    source_type: str
```

**GeoJSON format option** (`structures.py` lines 78-90) — reuse for GeoJSON export:
```python
    if format == "geojson":
        features = []
        for item in items:
            props = StructureResponse.model_validate(item).model_dump()
            geom = props.pop("geometry", None)
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": props,
            })
        return {"type": "FeatureCollection", "features": features}
```

**RBAC dependency injection** (new pattern — see Shared Patterns § Auth below):
```python
# Apply to every new route that requires auth:
@router.post("/structures/{id}/inspections")
async def create_inspection(
    body: InspectionCreate,
    current_user: UserModel = Depends(require_role("inspector")),
):
```

**Per-file guidance:**

| File | Route pattern to follow |
|---|---|
| `auth.py` | Follow `provenance.py` (simplest). Two endpoints: `POST /auth/token` (returns JWT), `GET /auth/me` (requires `Depends(get_current_user)`). Define `TokenRequest`/`TokenResponse` inline or import from `schemas/auth.py`. |
| `inspections.py` | Follow `structures.py`. Three endpoints: POST create (201, `require_role("inspector")`), GET list (all roles), GET detail (all roles). Path params: `/structures/{structure_id}/inspections` and `/structures/{structure_id}/inspections/{inspection_id}`. |
| `documents.py` | Follow `structures.py`. Four endpoints: POST register (201, `require_role("inspector")`), GET list (all roles), DELETE (`require_role("admin")`), GET download (all roles). |
| `risk.py` | Follow `structures.py`. Two endpoints: `POST /structures/{id}/override` (`require_role("engineer")`), `GET /structures/{id}/risk` (all roles). Override returns both system + override values. |
| `exports.py` | Follow `structures.py` GeoJSON pattern (lines 78-90) for GeoJSON export. Use `StreamingResponse` for CSV/PDF. Query params: `format`, `lang`, `type`, `district`, `condition`, `bbox`. |

---

### Service Pattern — applies to `auth_service.py`, `inspection_service.py`, `document_service.py`, `risk_service.py`

**Analog (full CRUD):** `apps/api/src/api/services/structure_service.py` (lines 1-372)
**Analog (simple CRUD):** `apps/api/src/api/services/provenance_service.py` (lines 1-108)

**Imports pattern** (`structure_service.py` lines 15-26):
```python
import uuid
from datetime import datetime

import structlog
from sqlalchemy import and_, desc, func, select

from api.infrastructure.database import async_session
from api.models.provenance import ProvenanceModel
from api.models.structure import StructureFactModel, StructureModel
from api.schemas.structures import StructureCreate, StructureUpdate

logger = structlog.get_logger(__name__)
```

**Create pattern** (`provenance_service.py` lines 24-52) — `async with async_session() as session` → `async with session.begin()` → `session.add()` → `session.flush()` → `session.refresh()`:
```python
async def create_provenance(
    source_type: str, confidence_level: str, ...
) -> ProvenanceModel:
    async with async_session() as session:
        async with session.begin():
            model = ProvenanceModel(
                source_type=source_type,
                confidence_level=confidence_level,
                ...
            )
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model
```

**Get by ID pattern** (`provenance_service.py` lines 55-70):
```python
async def get_provenance(provenance_id: uuid.UUID) -> ProvenanceModel | None:
    async with async_session() as session:
        result = await session.execute(
            select(ProvenanceModel).where(ProvenanceModel.id == provenance_id)
        )
        return result.scalar_one_or_none()
```

**List with filters pattern** (`provenance_service.py` lines 73-108):
```python
async def query_provenance(
    source_type: str | None = None, offset: int = 0, limit: int = 100,
) -> list[ProvenanceModel]:
    async with async_session() as session:
        stmt = select(ProvenanceModel)
        if source_type is not None:
            stmt = stmt.where(ProvenanceModel.source_type == source_type)
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
```

**Update with provenance + expiry pattern** (`structure_service.py` lines 257-351) — **critical for `risk_service.py` override logic**: expire current records (set `valid_to=now`), create new provenance, create new record:
```python
async def update_structure(structure_id, data, provenance_id) -> StructureModel | None:
    now = datetime.utcnow()
    async with async_session() as session:
        async with session.begin():
            # 1. Fetch existing
            result = await session.execute(
                select(StructureModel).where(StructureModel.id == structure_id)
            )
            structure = result.scalar_one_or_none()
            if structure is None:
                return None

            # 2. Create new provenance
            new_provenance = ProvenanceModel(
                source_type="manual",
                source_reference=f"api:update:{structure_id}",
                confidence_level="HIGH",
                contributor="api:update",
            )
            session.add(new_provenance)
            await session.flush()

            # 3. Expire existing facts (set valid_to=now)
            facts_result = await session.execute(
                select(StructureFactModel).where(
                    and_(
                        StructureFactModel.structure_id == structure_id,
                        StructureFactModel.valid_to.is_(None),
                    )
                )
            )
            for fact in facts_result.scalars().all():
                fact.valid_to = now

            # 4. Create new records ...
            # 5. Update model fields ...
            await session.flush()
            await session.refresh(structure)
            return structure
```

**Count + paginated list pattern** (`structure_service.py` lines 159-172):
```python
    async with async_session() as session:
        stmt = select(StructureModel).where(StructureModel.status != "deleted")
        stmt = _apply_attribute_filters(stmt, filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar() or 0
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        items = list(result.scalars().all())
        return items, total
```

**Per-file guidance:**

| File | Service pattern to follow |
|---|---|
| `auth_service.py` | Follow `provenance_service.py` (simplest). Functions: `get_user_by_username()`, `get_user_by_id()`, `get_user_by_api_key()`, `create_access_token()` (JWT encode — see RESEARCH.md lines 834-857), `decode_token()` (JWT decode). Token functions are pure (no DB). |
| `inspection_service.py` | Follow `structure_service.py`. Functions: `create_inspection()` (create with provenance + photos, trigger risk recomputation via Celery `.delay()`), `get_inspection()`, `list_inspections()`. Photo linking: create `InspectionPhotoModel` rows for each photo object key. |
| `document_service.py` | Follow `structure_service.py`. Functions: `register_document()` (create with provenance), `get_document()`, `list_documents()`, `delete_document()` (delete model + MinIO object via `minio_service.client.remove_object()`), `get_download_url()` (delegate to MinIOService). Access `app.state.minio` via request or pass MinIOService as param. |
| `risk_service.py` | Follow `structure_service.py` update pattern (lines 257-351). Functions: `get_latest_assessment()` (WHERE `valid_to IS NULL`), `create_assessment()` (create new, expire old), `create_override()` (see RESEARCH.md lines 596-654 for full pattern: expire current → create provenance → create override record with `is_override=True`), `recompute_risk_for_structure()` (load structure+facts+inspections → call `risk_engine.compute_risk()` → persist). |

---

### MinIO Integration Pattern — applies to `document_service.py`, `inspection_service.py`, `export_service.py`

**Analog:** `apps/api/src/api/services/minio_client.py` (lines 1-67) and `apps/api/src/api/routes/minio.py` (lines 1-60)

**MinIOService class** (`minio_client.py` lines 17-67) — already initialized in `main.py` lifespan as `app.state.minio`:
```python
class MinIOService:
    def __init__(self, endpoint, access_key, secret_key, secure):
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def ensure_bucket(self, bucket_name: str) -> None:
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def presigned_upload_url(self, bucket, object_name, expires=timedelta(hours=1)) -> str:
        return self.client.presigned_put_object(bucket, object_name, expires=expires)

    def presigned_download_url(self, bucket, object_name, expires=timedelta(hours=2)) -> str:
        return self.client.presigned_get_object(bucket, object_name, expires=expires)
```

**Presigned URL route pattern** (`routes/minio.py` lines 32-59) — existing endpoints reused for photo/document uploads. Access via `request.app.state.minio`:
```python
@router.post("/presign", response_model=PresignResponse)
async def presign_upload(body: PresignUploadRequest, request: Request) -> PresignResponse:
    minio_service = request.app.state.minio
    url = minio_service.presigned_upload_url(body.bucket, body.object_name)
    return PresignResponse(presigned_url=url, expires_in_seconds=3600)
```

**Lifespan initialization** (`main.py` lines 32-42) — MinIOService already created and buckets ensured:
```python
minio_service = MinIOService(
    endpoint=settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_use_ssl,
)
for bucket in _BUCKETS:  # ["sujoly-imagery", "sujoly-documents", "sujoly-photos"]
    minio_service.ensure_bucket(bucket)
app.state.minio = minio_service
```

**Buckets already created:** `sujoly-photos` (inspection photos), `sujoly-documents` (passports, reports). No new buckets needed.

**For PDF photo embedding** (`export_service.py`) — download from MinIO synchronously via `client.get_object()`, read bytes, base64 encode. Use `asyncio.to_thread()` to avoid blocking event loop (RESEARCH.md Pitfall 6):
```python
# Pattern for photo download in export_service:
response = minio_service.client.get_object(photo.minio_bucket, photo.minio_object_key)
photo_bytes = response.read()
photo_base64 = base64.b64encode(photo_bytes).decode()
```

---

### Migration Pattern — applies to `0003_risk_inspection_document_tables.py`

**Analog:** `apps/api/alembic/versions/0001_initial.py` (lines 1-94)

**Migration header pattern** (lines 17-29):
```python
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
```

**Create table with FK + CheckConstraint** (lines 35-47):
```python
op.create_table(
    "provenance",
    sa.Column("id", Uuid, primary_key=True),
    sa.Column("source_type", sa.String(50), nullable=False),
    sa.Column("confidence_level", sa.String(10), nullable=False, server_default="HIGH"),
    sa.CheckConstraint(
        "confidence_level IN ('HIGH', 'MEDIUM', 'LOW')",
        name="ck_provenance_confidence_level",
    ),
)
```

**Create table with FK constraints** (lines 51-63):
```python
op.create_table(
    "structures",
    sa.Column("id", Uuid, primary_key=True),
    sa.Column("type", sa.String(100), nullable=False),
    sa.Column("provenance_id", Uuid, nullable=False),
    sa.ForeignKeyConstraint(["provenance_id"], ["provenance.id"]),
)
```

**Create indexes** (line 48, 82):
```python
op.create_index("ix_provenance_source_type", "provenance", ["source_type"])
op.create_index("ix_structure_facts_structure_id", "structure_facts", ["structure_id"])
```

**Raw SQL for special indexes** (line 65):
```python
op.execute(
    "CREATE INDEX ix_structures_geometry ON structures USING GIST (geometry)"
)
```

**Downgrade pattern** (lines 85-94) — reverse order, drop indexes before tables:
```python
def downgrade() -> None:
    op.drop_index("ix_structure_facts_structure_id", table_name="structure_facts")
    op.drop_table("structure_facts")
    op.drop_index("ix_provenance_source_type", table_name="provenance")
    op.drop_table("provenance")
```

**Migration 0003 must create (in dependency order):**
1. `users` table (no FK deps) — with `CheckConstraint` on role
2. `inspections` table (FK → structures, FK → provenance) — with `CheckConstraint` on condition_at_inspection if needed
3. `inspection_photos` table (FK → inspections, FK → provenance)
4. `documents` table (FK → structures nullable, FK → provenance) — with `CheckConstraint` on document_type and language
5. `risk_assessments` table (FK → structures, FK → provenance) — with `CheckConstraint` on inspection_interval and repair_status enums

---

### Test Pattern — applies to all 6 new test files + `conftest.py` modification

**Analog:** `apps/api/tests/test_structures.py` (lines 1-258) and `apps/api/tests/conftest.py` (lines 1-200)

**Test imports** (`test_structures.py` lines 17-21):
```python
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
```

**Test class structure** (`test_structures.py` lines 24-26):
```python
class TestStructureEndpoints:
    """Tests for /api/v1/structures CRUD + search endpoints."""
```

**Mock factory pattern** (`test_structures.py` lines 27-52, `conftest.py` lines 157-182):
```python
def _mock_structure(self, **overrides):
    defaults = {
        "id": uuid.uuid4(),
        "name_ru": "Канал 1",
        "type": "canal",
        "provenance_id": uuid.uuid4(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, val in defaults.items():
        setattr(mock, key, val)
    return mock
```

**Service patch + TestClient pattern** (`test_structures.py` lines 58-79):
```python
def test_create_structure(self, test_client):
    mock_struct = self._mock_structure()
    prov_id = uuid.uuid4()
    with patch(
        "api.routes.structures.create_structure",
        AsyncMock(return_value=mock_struct),
    ):
        response = test_client.post(
            f"/api/v1/structures?provenance_id={prov_id}",
            json={"type": "canal", "name_ru": "Канал 1"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["name_ru"] == "Канал 1"
```

**404 test pattern** (`test_structures.py` lines 96-104):
```python
def test_get_structure_not_found(self, test_client):
    non_existent_id = uuid.uuid4()
    with patch(
        "api.routes.structures.get_structure",
        AsyncMock(return_value=None),
    ):
        response = test_client.get(f"/api/v1/structures/{non_existent_id}")
    assert response.status_code == 404
```

**conftest.py test_client fixture** (`conftest.py` lines 98-110) — patches MinIO for lifespan:
```python
@pytest.fixture
def test_client(mock_healthy_minio):
    with patch("api.services.minio_client.Minio", mock_healthy_minio):
        from api.main import app
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            yield client
```

**conftest.py mock fixtures** (`conftest.py` lines 20-88) — pattern for new mock fixtures:
```python
@pytest.fixture
def mock_healthy_db():
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=MagicMock())
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return MagicMock(return_value=mock_cm)
```

**Per-file guidance:**

| File | Test pattern |
|---|---|
| `test_risk_engine.py` | **Pure unit tests — no DB mocks needed.** Import `risk_engine` directly, call `compute_risk()` with dict inputs, assert on returned `RiskAssessment` fields. Test: condition score blend, interval mapping bands, red-flag detection, repair status thresholds, weak-evidence floor. This is the most critical test file. |
| `test_auth.py` | Unit: JWT encode/decode (call `create_access_token` + `decode_token`, assert claims). Integration: mock `auth_service.get_user_by_*` with `AsyncMock`, test `POST /auth/token` and `GET /auth/me` via TestClient. Test `require_role` dependency with different roles. |
| `test_risk_api.py` | Follow `test_structures.py` pattern. Mock `risk_service.create_override` and `risk_service.get_latest_assessment`. Test `POST /structures/{id}/override` with engineer role (200) and viewer role (403). Test `GET /structures/{id}/risk` returns full breakdown. |
| `test_inspections.py` | Follow `test_structures.py` pattern. Mock `inspection_service.create_inspection` / `list_inspections` / `get_inspection`. Test 201 on create, 200 on list, 404 on not found. Test photo metadata in response. |
| `test_documents.py` | Follow `test_structures.py` pattern. Mock `document_service.*`. Test register (201), list (200), delete (admin only → test 403 for inspector), download URL generation. |
| `test_exports.py` | Mock `export_service.*` or `structure_service.list_structures`. Test CSV response has `text/csv` media type + BOM. Test GeoJSON returns `FeatureCollection`. Test PDF returns `application/pdf`. Test `lang` param affects headers. |
| `conftest.py` *(modify)* | Add fixtures: `mock_user` (with role field), `mock_inspection`, `mock_document`, `mock_risk_assessment` (with all factor fields), `mock_risk_assessment_override` (with `is_override=True`). Add `mock_auth_token` fixture for authenticated requests. |

---

## Shared Patterns

### Authentication (NEW — no codebase analog, from RESEARCH.md Pattern 1)

**Source:** RESEARCH.md lines 319-383 (Pattern 1: FastAPI RBAC with JWT)
**Apply to:** `apps/api/src/api/dependencies/auth.py` (new file), all route files that require auth

**OAuth2PasswordBearer + JWT decode + role enforcement** — full reference code:
```python
# apps/api/src/api/dependencies/auth.py
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from api.config.settings import settings
from api.models.user import UserModel
from api.services.auth_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user_by_id(uuid.UUID(user_id))
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
```

**JWT encode pattern** (RESEARCH.md lines 834-857) — for `auth_service.py`:
```python
def create_access_token(user_id: str, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {"user_id": user_id, "username": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
```

### Error Handling (EXISTING — apply to all new routes)

**Source:** `apps/api/src/api/main.py` lines 63-82 (global exception handler) + `routes/structures.py` (HTTPException pattern)

**Global handler already exists** — new routes just raise `HTTPException`:
```python
# main.py lines 63-82 — already handles all exceptions:
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    logger.exception("unhandled_exception", ...)
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
```

**Route-level error pattern** — raise HTTPException for 404/400/403:
```python
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"...")
raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
```

### Provenance (EXISTING — apply to all new services that create records)

**Source:** `apps/api/src/api/services/structure_service.py` lines 292-299 and `apps/api/src/api/models/provenance.py`

**Every new record with provenance must:**
1. Create a `ProvenanceModel` with `source_type`, `confidence_level`, `contributor`, `source_reference`
2. `session.add(provenance)` → `await session.flush()` to get the ID
3. Use `provenance.id` as FK on the new record

```python
# Pattern from structure_service.py lines 292-299:
new_provenance = ProvenanceModel(
    source_type="manual",  # or "inspection", "api:override", etc.
    source_reference=f"api:update:{structure_id}",
    confidence_level="HIGH",
    contributor="api:update",  # or user.username for authenticated operations
)
session.add(new_provenance)
await session.flush()
# Then use new_provenance.id as FK
```

**Provenance source_type values** (from `provenance.py` line 22): `kazvodhoz_spreadsheet`, `osm`, `satellite`, `ocr`, `manual`, `ai_inferred`, `inspection`. Phase 3 adds: `inspection` (for inspection records), `manual` (for engineer overrides).

### Celery Task Pattern (EXISTING — extend for risk recomputation)

**Source:** `apps/api/src/api/tasks/celery_tasks.py` (lines 1-36) and `apps/api/src/api/celery_app.py` (lines 1-20)

**Task definition pattern** (`celery_tasks.py` lines 9-18, 21-36):
```python
@celery_app.task
def health_check_task():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@celery_app.task(bind=True, name="ingest_kazvodhoz")
def ingest_kazvodhoz_task(self, filepath: str = "датасет.xls", force: bool = False):
    return bulk_insert_structures(filepath=filepath, force=force)
```

**Celery app config** (`celery_app.py` lines 7-20) — add Beat schedule:
```python
celery_app = Celery(
    "sujoly_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["api.tasks.celery_tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
# ADD (from RESEARCH.md lines 886-898):
from celery.schedules import crontab
celery_app.conf.beat_schedule = {
    'daily-risk-recomputation': {
        'task': 'api.tasks.celery_tasks.recompute_all_risks',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

**Event-driven task dispatch** (from `routes/ingestion.py` line 74) — use `.delay()` to enqueue:
```python
# In inspection_service.py after creating inspection:
recompute_structure_risk.delay(structure_id=str(structure_id))
```

### Config/Settings Modification Pattern

**Source:** `apps/api/src/api/config/settings.py` (lines 1-50)

**Add JWT settings** — follow existing pattern with `API_` env prefix:
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_", ...)

    # EXISTING settings...
    database_url: str = "..."
    redis_url: str = "..."

    # ADD (Phase 3):
    jwt_secret: str = ""  # Must be set in .env — use openssl rand -hex 32
    jwt_expiry_hours: int = 24
    initial_admin_username: str = "admin"
    initial_admin_api_key: str = ""  # Must be set in .env
```

### Main.py Router Registration Pattern

**Source:** `apps/api/src/api/main.py` lines 17-18, 124-128

**Import and register new routers:**
```python
# Line 17 — add new imports:
from api.routes import auth, documents, exports, health, ingestion, inspections, minio, provenance, risk, structures

# Lines 124-128 — add new router registrations:
app.include_router(auth.router)
app.include_router(inspections.router)
app.include_router(documents.router)
app.include_router(risk.router)
app.include_router(exports.router)
```

**Seed admin user in lifespan** (after MinIO init, lines 39-41) — new code block:
```python
# After app.state.minio = minio_service, add:
# Seed initial admin user if none exists (D-10/D-11, RESEARCH.md Open Question 1)
async with async_session() as session:
    result = await session.execute(
        select(UserModel).where(UserModel.role == "admin").limit(1)
    )
    if result.scalar_one_or_none() is None:
        admin = UserModel(
            username=settings.initial_admin_username,
            role="admin",
            api_key=settings.initial_admin_api_key,
        )
        session.add(admin)
        await session.commit()
        logger.info("initial_admin_seeded", username=admin.username)
```

### Docker/Env Modification Patterns

**docker-compose.yml** — add `celery-beat` service (follow `celery-worker` pattern, lines 89-113):
```yaml
  celery-beat:
    build:
      context: ./apps/api
    command: celery -A api.celery_app beat --loglevel=info
    environment:
      # Same env vars as celery-worker (lines 93-100)
      API_DATABASE_URL: postgresql+asyncpg://...
      API_REDIS_URL: redis://redis:6379/0
      API_MINIO_ENDPOINT: minio:9000
      # ADD JWT env vars:
      API_JWT_SECRET: ${API_JWT_SECRET}
      API_JWT_EXPIRY_HOURS: "24"
      API_INITIAL_ADMIN_USERNAME: ${API_INITIAL_ADMIN_USERNAME:-admin}
      API_INITIAL_ADMIN_API_KEY: ${API_INITIAL_ADMIN_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

**Also add JWT env vars to `api` service** (lines 66-74) and `celery-worker` (lines 93-100).

**Dockerfile** — add WeasyPrint system deps (RESEARCH.md lines 172-182), insert after existing `apt-get` (line 24-26):
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

**pyproject.toml** — add to `dependencies` list (lines 6-24):
```toml
dependencies = [
    # ...existing...
    "weasyprint>=69.0",
    "pyjwt>=2.13.0",
    "jinja2>=3.1.6",
]
```

**.env.example** — add after line 17 (`API_ALLOWED_ORIGINS`):
```env
# ---- JWT Auth (Phase 3) ----
API_JWT_SECRET=  # Generate with: openssl rand -hex 32
API_JWT_EXPIRY_HOURS=24
API_INITIAL_ADMIN_USERNAME=admin
API_INITIAL_ADMIN_API_KEY=  # Generate with: openssl rand -hex 32
```

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason | Reference |
|---|---|---|---|---|
| `apps/api/src/api/services/risk_engine.py` | service (pure Python) | transform | No pure computation module exists — all services are DB-backed async | RESEARCH.md lines 385-589 (Pattern 2: full reference implementation with `RiskAssessment` dataclass, `compute_condition_score()`, `detect_red_flags()`, `compute_risk()`) |
| `apps/api/src/api/services/export_service.py` | service | streaming + file-I/O | No streaming/file-generation service exists | RESEARCH.md lines 658-747 (Pattern 4: CSV StreamingResponse, Pattern 5: WeasyPrint PDF). GeoJSON export reuses `structures.py` lines 78-90. |
| `apps/api/src/api/dependencies/auth.py` | middleware | request-response | No auth/RBAC exists in codebase | RESEARCH.md lines 319-383 (Pattern 1: full `get_current_user` + `require_role` implementation) + lines 834-857 (JWT encode/decode) |
| `apps/api/templates/inspection_report_ru.html` | template | file-I/O | No HTML templates exist in project | RESEARCH.md lines 698-747 (Pattern 5: Jinja2 template structure — structure identity, inspection details, findings, photos, risk summary) |
| `apps/api/templates/inspection_report_kk.html` | template | file-I/O | Same as above | Same as above — Kazakh Cyrillic variant |
| `apps/api/templates/inspection_report_en.html` | template | file-I/O | Same as above | Same as above — English variant |

---

## Metadata

**Analog search scope:**
- `apps/api/src/api/models/` — 2 model files scanned
- `apps/api/src/api/schemas/` — 1 schema file scanned
- `apps/api/src/api/services/` — 4 service files scanned
- `apps/api/src/api/routes/` — 5 route files scanned
- `apps/api/src/api/config/` — 1 settings file scanned
- `apps/api/src/api/infrastructure/` — 1 database file scanned
- `apps/api/src/api/tasks/` — 1 task file scanned
- `apps/api/src/api/utils/` — 1 logging file scanned
- `apps/api/alembic/versions/` — 2 migration files scanned
- `apps/api/tests/` — 2 test files + conftest scanned
- `apps/api/` root — `pyproject.toml`, `Dockerfile` scanned
- Project root — `docker-compose.yml`, `.env.example` scanned

**Files scanned:** 23 existing source files + 7 config/infra files
**Pattern extraction date:** 2026-06-26
**Strongest analogs:** `structure_service.py` (service CRUD+provenance+expiry pattern), `structures.py` route (APIRouter+HTTPException+GeoJSON pattern), `0001_initial.py` (migration create_table+FK+CheckConstraint pattern)
