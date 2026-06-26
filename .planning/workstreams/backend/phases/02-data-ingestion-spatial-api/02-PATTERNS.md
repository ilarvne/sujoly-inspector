# Phase 2: Data Ingestion & Spatial API - Pattern Map

**Mapped:** 2026-06-26
**Files analyzed:** 16 (9 new + 6 modified + 1 verified-no-change)
**Analogs found:** 14 / 16

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `apps/api/alembic/versions/0002_add_filterable_columns_and_search.py` | migration | transform (DDL) | `apps/api/alembic/versions/0001_initial.py` | exact |
| `apps/api/src/api/models/structure.py` (modify) | model | CRUD | `apps/api/src/api/models/structure.py` (itself) + `apps/api/src/api/models/provenance.py` | exact (self-modification) |
| `apps/api/src/api/schemas/structures.py` | schema | request-response | `apps/api/src/api/routes/provenance.py` (inline Pydantic models) | role-match (no schemas/ dir exists) |
| `apps/api/src/api/routes/structures.py` | route | request-response | `apps/api/src/api/routes/provenance.py` | exact |
| `apps/api/src/api/routes/ingestion.py` | route | request-response (async job trigger) | `apps/api/src/api/routes/provenance.py` | exact |
| `apps/api/src/api/services/structure_service.py` | service | CRUD | `apps/api/src/api/services/provenance_service.py` | exact |
| `apps/api/src/api/services/ingestion_service.py` | service | batch (xlrd parse + psycopg bulk insert) | `apps/api/src/api/services/provenance_service.py` | partial (service layer pattern; no sync/bulk service exists) |
| `apps/api/src/api/tasks/celery_tasks.py` (modify) | service (Celery task) | batch | `apps/api/src/api/tasks/celery_tasks.py` (itself) + `apps/api/src/api/celery_app.py` | exact (self-modification) |
| `apps/api/src/api/main.py` (modify) | config | request-response | `apps/api/src/api/main.py` (itself) | exact (self-modification) |
| `docker-compose.yml` (modify) | config | request-response | `docker-compose.yml` (itself) | exact (self-modification) |
| `docker/postgres/init-extensions.sql` (verify) | config | transform (DDL) | — | no change needed (pg_trgm already enabled) |
| `.env.example` (modify) | config | config | `.env.example` (itself) | exact (self-modification) |
| `apps/api/tests/test_structures.py` | test | request-response | `apps/api/tests/test_provenance.py` | exact |
| `apps/api/tests/test_ingestion.py` | test | batch | `apps/api/tests/test_provenance.py` | role-match (test structure; no Celery test exists) |
| `apps/api/tests/test_tipg.py` | test | request-response (integration) | `apps/api/tests/test_provenance.py` | role-match (integration marker pattern) |
| `apps/api/tests/conftest.py` (modify) | test (config) | config | `apps/api/tests/conftest.py` (itself) | exact (self-modification) |

---

## Pattern Assignments

### `apps/api/alembic/versions/0002_add_filterable_columns_and_search.py` (migration, transform)

**Analog:** `apps/api/alembic/versions/0001_initial.py`

**Revision identifiers pattern** (lines 17-29):
```python
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
```

**Core migration pattern** — `op.create_table` with typed columns (lines 35-47):
```python
def upgrade() -> None:
    op.create_table(
        "provenance",
        sa.Column("id", Uuid, primary_key=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.Text, nullable=True),
        sa.Column("confidence_level", sa.String(10), nullable=False, server_default="HIGH"),
    )
    op.create_index("ix_provenance_source_type", "provenance", ["source_type"])
```

**Raw SQL via `op.execute` for PostGIS indexes** (lines 64-67):
```python
    # GiST spatial index on geometry column (PostGIS requirement)
    op.execute(
        "CREATE INDEX ix_structures_geometry ON structures USING GIST (geometry)"
    )
```

**Downgrade pattern** — reverse order, drop indexes before tables (lines 85-94):
```python
def downgrade() -> None:
    op.drop_index("ix_structure_facts_structure_id", table_name="structure_facts")
    op.drop_table("structure_facts")
    op.execute("DROP INDEX IF EXISTS ix_structures_geometry")
    op.drop_table("structures")
```

**What to copy for 0002:**
- Use `op.execute("ALTER TABLE structures ALTER COLUMN geometry DROP NOT NULL")` for nullable geometry (Pitfall #7 — raw SQL preserves GiST index)
- Use `op.add_column("structures", sa.Column(...))` for the 7 new filterable columns (D-08)
- Use `op.execute("""ALTER TABLE ... ADD COLUMN ... GENERATED ALWAYS AS (...) STORED""")` for tsvector columns (D-10)
- Use `op.execute("CREATE INDEX ... USING GIN (...)")` for GIN indexes on tsvector + trigram
- Use `op.create_index(...)` for B-tree indexes on filterable columns
- Downgrade: drop indexes first, then drop columns, then restore NOT NULL

**Reference implementation:** RESEARCH.md lines 738-833 provides the complete 0002 migration code.

---

### `apps/api/src/api/models/structure.py` (model, CRUD — MODIFY)

**Analog:** `apps/api/src/api/models/structure.py` (itself) + `apps/api/src/api/models/provenance.py`

**Existing model pattern** — SQLAlchemy 2.0 Mapped types (lines 12-49):
```python
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.database import Base


class StructureModel(Base):
    __tablename__ = "structures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name_ru: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name_kk: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    geometry = mapped_column(Geometry("Point", srid=4326), nullable=False)  # ← change to nullable=True
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

**Provenance model pattern** — CheckConstraint + indexed columns (from `provenance.py` lines 29-46):
```python
    __table_args__ = (
        CheckConstraint(
            "confidence_level IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_provenance_confidence_level",
        ),
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
```

**What to modify in structure.py:**
- Change `geometry` line 37: `nullable=False` → `nullable=True` (D-02)
- Add 7 filterable columns after `type` (D-08): `district`, `water_source`, `technical_condition`, `wear_percentage` (Float), `commissioning_year` (Integer), `cadastral_number`, `structure_count` (Integer)
- **Do NOT add tsvector columns as ORM Mapped types** — they are GENERATED columns created by Alembic migration raw SQL. The ORM model does not need to declare them (they're computed by PostgreSQL, not written by the application). If read access is needed, add as `Mapped[str | None]` with `mapped_column(TSVECTOR, nullable=True)` — but SQLAlchemy has no native TSVECTOR type, so use `from sqlalchemy.types import TypeDecorator` or simply omit from the model and access via raw SQL in the service layer.
- Import additions: `from sqlalchemy import Float, Integer`

---

### `apps/api/src/api/schemas/structures.py` (schema, request-response — NEW)

**Analog:** Inline Pydantic models in `apps/api/src/api/routes/provenance.py`

> **Note:** No `schemas/` directory exists in the codebase. The provenance route defines Pydantic models inline. RESEARCH.md (line 221) recommends a separate `schemas/structures.py` file. The planner should decide: inline models (matching provenance pattern) or separate schemas file (RESEARCH.md recommendation). If separate, copy the Pydantic patterns below.

**Pydantic Create model pattern** (from `provenance.py` lines 27-45):
```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class ProvenanceCreate(BaseModel):
    """Request body for creating a provenance record."""

    source_type: str = Field(..., description="Source type: kazvodhoz_spreadsheet, osm, ...")
    source_reference: str | None = Field(None, description="URL, file path, OSM element ID, ...")
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field("HIGH", description="Confidence level")
    contributor: str | None = Field(None, description="Person, system, or process")
```

**Pydantic Response model pattern** (from `provenance.py` lines 48-58):
```python
class ProvenanceResponse(BaseModel):
    """Response model for a provenance record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: str
    source_reference: str | None
    confidence_level: str
    contributor: str | None
    recorded_at: datetime
```

**What to create for structures schemas:**
- `StructureCreate(BaseModel)` — name_ru, type, district, water_source, etc. (all filterable fields from D-08)
- `StructureUpdate(BaseModel)` — same fields but all Optional
- `StructureResponse(BaseModel)` with `model_config = ConfigDict(from_attributes=True)` — all fields + id + provenance_id + geometry as `dict | None`
- `StructureListResponse(BaseModel)` — `items: list[StructureResponse]`, `total: int`, `offset: int`, `limit: int` (D-16 pagination envelope)
- `SearchResultResponse(BaseModel)` — extends StructureResponse with `match_score: float` field
- `IngestionJobResponse(BaseModel)` — `job_id: str`, `status: str` (D-15)

**Reference implementation:** RESEARCH.md lines 479-535 provides StructureResponse and StructureListResponse code.

---

### `apps/api/src/api/routes/structures.py` (route, request-response — NEW)

**Analog:** `apps/api/src/api/routes/provenance.py`

**Imports + router setup pattern** (lines 11-24):
```python
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from api.services.provenance_service import (
    create_provenance,
    get_provenance,
    query_provenance,
)

router = APIRouter(prefix="/api/v1", tags=["provenance"])
```

**POST create endpoint pattern** (lines 61-74):
```python
@router.post(
    "/provenance",
    response_model=ProvenanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_provenance_endpoint(body: ProvenanceCreate) -> ProvenanceResponse:
    """Create a new provenance record."""
    model = await create_provenance(
        source_type=body.source_type,
        confidence_level=body.confidence_level,
        source_reference=body.source_reference,
        contributor=body.contributor,
    )
    return ProvenanceResponse.model_validate(model)
```

**GET by ID + 404 pattern** (lines 77-89):
```python
@router.get("/provenance/{provenance_id}", response_model=ProvenanceResponse)
async def get_provenance_endpoint(provenance_id: uuid.UUID) -> ProvenanceResponse:
    """Retrieve a provenance record by ID."""
    model = await get_provenance(provenance_id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provenance record '{provenance_id}' not found",
        )
    return ProvenanceResponse.model_validate(model)
```

**GET list with filters + pagination pattern** (lines 92-118):
```python
@router.get("/provenance", response_model=list[ProvenanceResponse])
async def list_provenance_endpoint(
    source_type: str | None = None,
    confidence_level: str | None = None,
    recorded_after: datetime | None = None,
    recorded_before: datetime | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[ProvenanceResponse]:
    """Query provenance records with optional filters."""
    models = await query_provenance(
        source_type=source_type,
        confidence_level=confidence_level,
        recorded_after=recorded_after,
        recorded_before=recorded_before,
        offset=offset,
        limit=limit,
    )
    return [ProvenanceResponse.model_validate(m) for m in models]
```

**What to copy for structures.py:**
- `router = APIRouter(prefix="/api/v1", tags=["structures"])`
- Import service functions from `api.services.structure_service`
- `GET /structures` — list with type, district, technical_condition, water_source, q, lang, bbox, offset, limit, format params (D-16)
- `GET /structures/search` — search endpoint with FTS + trigram (D-14)
- `GET /structures/{id}` — detail with 404 handling
- `POST /structures` — create with 201 status
- `PUT /structures/{id}` — update
- `DELETE /structures/{id}` — delete (soft or hard, per D-13)
- Use `Query(...)` for required params, `Query(None, description="...")` for optional
- Use `Literal["ru", "kk", "en"]` for lang param
- Use `Literal["json", "geojson"]` for format param

**Reference implementation:** RESEARCH.md lines 466-535 provides route code for list and search endpoints.

---

### `apps/api/src/api/routes/ingestion.py` (route, request-response — NEW)

**Analog:** `apps/api/src/api/routes/provenance.py`

**What to create:**
- `router = APIRouter(prefix="/api/v1", tags=["ingestion"])`
- `POST /ingestion/kazvodhoz` — accepts optional `UploadFile` (defaults to bundled `датасет.xls`), triggers Celery task via `.delay()`, returns `{"job_id": task.id}` immediately (D-15)
- `GET /ingestion/kazvodhoz/{job_id}` — polls `AsyncResult(job_id)` from Celery, returns `{"status": ..., "result": ...}`

**File upload pattern** (from FastAPI, not in existing codebase):
```python
from fastapi import APIRouter, UploadFile, File, Query
from api.tasks.celery_tasks import ingest_kazvodhoz_task

@router.post("/ingestion/kazvodhoz")
async def trigger_ingestion(
    file: UploadFile | None = File(None, description="Optional .xls file upload"),
    force: bool = Query(False, description="Re-ingest even if records exist"),
):
    filepath = "датасет.xls"  # default bundled file
    if file:
        # Save uploaded file to temp location
        ...
    task = ingest_kazvodhoz_task.delay(filepath=filepath, force=force)
    return {"job_id": task.id, "status": "queued"}
```

**Job status polling pattern:**
```python
from celery.result import AsyncResult
from api.celery_app import celery_app

@router.get("/ingestion/kazvodhoz/{job_id}")
async def get_ingestion_status(job_id: str):
    result = AsyncResult(job_id, app=celery_app)
    return {"job_id": job_id, "status": result.status, "result": result.result if result.ready() else None}
```

---

### `apps/api/src/api/services/structure_service.py` (service, CRUD — NEW)

**Analog:** `apps/api/src/api/services/provenance_service.py`

**Imports + logger pattern** (lines 12-21):
```python
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select

from api.infrastructure.database import async_session
from api.models.provenance import ProvenanceModel

logger = structlog.get_logger(__name__)
```

**Create pattern — async_session + session.begin + add/flush/refresh** (lines 24-52):
```python
async def create_provenance(
    source_type: str,
    confidence_level: str,
    source_reference: str | None = None,
    contributor: str | None = None,
) -> ProvenanceModel:
    async with async_session() as session:
        async with session.begin():
            model = ProvenanceModel(
                source_type=source_type,
                confidence_level=confidence_level,
                source_reference=source_reference,
                contributor=contributor,
            )
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model
```

**Get by ID pattern** (lines 55-70):
```python
async def get_provenance(provenance_id: uuid.UUID) -> ProvenanceModel | None:
    async with async_session() as session:
        result = await session.execute(
            select(ProvenanceModel).where(ProvenanceModel.id == provenance_id)
        )
        return result.scalar_one_or_none()
```

**Query with optional filters pattern** (lines 73-108):
```python
async def query_provenance(
    source_type: str | None = None,
    confidence_level: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[ProvenanceModel]:
    async with async_session() as session:
        stmt = select(ProvenanceModel)
        if source_type is not None:
            stmt = stmt.where(ProvenanceModel.source_type == source_type)
        if confidence_level is not None:
            stmt = stmt.where(ProvenanceModel.confidence_level == confidence_level)
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
```

**What to copy for structure_service.py:**
- Same `async with async_session() as session` + `session.begin()` pattern for create
- Same `select().where()` + optional filter chaining for list/query
- Add `from api.models.structure import StructureModel, StructureFactModel`
- Add `from geoalchemy2 import functions as geofunc` + `from sqlalchemy import func, and_` for bbox spatial filtering
- Add `select(func.count()).select_from(stmt.subquery())` for total count (D-16 pagination)
- For search: use `func.ts_rank_cd()` + `func.similarity()` in the select to compute blended score (D-12). Use `op.execute()` with raw SQL or SQLAlchemy `text()` for the combined FTS + trigram query.
- Return tuples of `(model, score)` from search, or add a `match_score` attribute

**bbox spatial filter reference:** RESEARCH.md lines 836-876 provides the `ST_MakeEnvelope` + `ST_Intersects` pattern.

**Combined FTS + trigram search reference:** RESEARCH.md lines 307-321 provides the blended score SQL query.

---

### `apps/api/src/api/services/ingestion_service.py` (service, batch — NEW)

**Analog:** `apps/api/src/api/services/provenance_service.py` (service layer pattern, partial match)

> **No existing sync/bulk-insert service exists in the codebase.** The provenance service uses async SQLAlchemy. The ingestion service uses sync psycopg for bulk loading (D-17). Use RESEARCH.md Pattern 4 (lines 366-463) as the primary reference, with the provenance service's import/logging patterns.

**Import pattern to follow** (from `provenance_service.py` lines 12-21):
```python
import structlog
from sqlalchemy import select
from api.models.provenance import ProvenanceModel

logger = structlog.get_logger(__name__)
```

**Sync database URL already available** (from `settings.py` lines 33-34):
```python
    sync_database_url: str = "postgresql+psycopg://sujoly:sujoly_dev@postgres:5432/sujoly"
```

**What to create for ingestion_service.py:**
- Import `from sqlalchemy import create_engine, select` + `from sqlalchemy.orm import Session`
- Import `from api.config.settings import settings` for `settings.sync_database_url`
- Import `from api.models.structure import StructureModel, StructureFactModel` + `from api.models.provenance import ProvenanceModel`
- Import `import xlrd`
- `parse_kazvodhoz_sheet(sheet)` — skip header/summary rows, handle float-to-int conversion (Pitfall #1, #2)
- `enrich_with_cross_sheet_data(records, sheet_kanaly, sheet_list1)` — join by row number (Pitfall #3)
- `bulk_insert_structures(records, force=False)` — sync Session, idempotency check on source_reference (D-19), create provenance + structure + facts per record (D-20, D-07)
- Use `structlog.get_logger(__name__)` for logging
- Use `session.commit()` at end (not per-row)

**Reference implementation:** RESEARCH.md lines 370-463 provides the complete Celery task with sync Session pattern. RESEARCH.md lines 620-734 provides the xlrd parsing + cross-sheet enrichment functions.

---

### `apps/api/src/api/tasks/celery_tasks.py` (service, batch — MODIFY)

**Analog:** `apps/api/src/api/tasks/celery_tasks.py` (itself) + `apps/api/src/api/celery_app.py`

**Existing task pattern** (celery_tasks.py lines 1-17):
```python
"""Celery task definitions for the SuJoly Inspector API."""

from datetime import datetime, timezone

from api.celery_app import celery_app


@celery_app.task
def health_check_task():
    """Simple task to verify Celery + Redis are working."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

**Celery app config** (celery_app.py lines 7-20):
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
```

**What to add to celery_tasks.py:**
- Import ingestion_service functions: `from api.services.ingestion_service import bulk_insert_structures`
- Add `ingest_kazvodhoz_task` with `bind=True` for `self` access (progress reporting):
```python
@celery_app.task(bind=True, name="ingest_kazvodhoz")
def ingest_kazvodhoz_task(self, filepath: str = "датасет.xls", force: bool = False):
    """Ingest Kazvodhoz spreadsheet into PostGIS."""
    # Call ingestion_service.bulk_insert_structures(filepath, force)
    # Update self.update_state(state="PROGRESS", meta={"current": n, "total": total})
    # Return {"inserted": N, "skipped": N, "total": N}
```
- The `include=["api.tasks.celery_tasks"]` in celery_app.py already ensures this module is loaded — no change to celery_app.py needed.

**Reference implementation:** RESEARCH.md lines 381-462 provides the full task implementation.

---

### `apps/api/src/api/main.py` (config, request-response — MODIFY)

**Analog:** `apps/api/src/api/main.py` (itself)

**Router registration pattern** (lines 15-19, 124-126):
```python
from api.routes import health, minio, provenance
# ...
app.include_router(health.router)
app.include_router(provenance.router)
app.include_router(minio.router)
```

**What to modify:**
- Add `structures` and `ingestion` to the import: `from api.routes import health, ingestion, minio, provenance, structures`
- Add after existing `include_router` calls:
```python
app.include_router(structures.router)
app.include_router(ingestion.router)
```

**Global exception handler** (lines 63-82) — already handles HTTPException and unhandled errors. No change needed; new routes inherit this behavior.

---

### `docker-compose.yml` (config, request-response — MODIFY)

**Analog:** `docker-compose.yml` (itself)

**Existing service pattern** — postgres (lines 6-29):
```yaml
  postgres:
    build:
      context: ./docker/postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-sujoly}
      POSTGRES_USER: ${POSTGRES_USER:-sujoly}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-sujoly_dev}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB} && ..."]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
```

**App service pattern** — depends_on with service_healthy (lines 75-81):
```yaml
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
```

**What to add — TiPG service:**
- Add after `celery-worker` service, before `volumes:`
- Use `image: ghcr.io/developmentseed/tipg:latest`
- Environment: `DATABASE_URL` (NOT `TIPG_DATABASE_URL` — Pitfall #4), `TIPG_CORS_ORIGIN`, `TIPG_DEFAULT_FEATURES_LIMIT`, `TIPG_MAX_FEATURES_PER_QUERY`, `TIPG_CATALOG_TTL`
- Port 8080
- `depends_on: postgres: condition: service_healthy`
- Healthcheck: `curl -f http://localhost:8080/healthz.html`

**Reference implementation:** RESEARCH.md lines 330-356 provides the complete TiPG service YAML.

---

### `docker/postgres/init-extensions.sql` (config — NO CHANGE NEEDED)

**Current content** (lines 1-8):
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

**pg_trgm is already enabled on line 8.** No modification needed. The Alembic migration 0002 can assume `pg_trgm` is available for trigram indexes.

---

### `.env.example` (config — MODIFY)

**Analog:** `.env.example` (itself)

**Existing API env vars pattern** (lines 10-17):
```
API_DATABASE_URL=postgresql+asyncpg://sujoly:sujoly_dev@postgres:5432/sujoly
API_SYNC_DATABASE_URL=postgresql+psycopg://sujoly:sujoly_dev@postgres:5432/sujoly
API_REDIS_URL=redis://redis:6379/0
```

**Existing DATABASE_URL** (line 25):
```
DATABASE_URL=postgresql://USER:PASSWORD@HOST/PORT/DB
```

**What to add — TiPG section:**
```env
# ---- TiPG (OGC API Features + Tiles) ----
# TiPG uses DATABASE_URL (not TIPG_DATABASE_URL) for DB connection (Pitfall #4)
TIPG_CORS_ORIGIN=*
TIPG_DEFAULT_FEATURES_LIMIT=1000
TIPG_MAX_FEATURES_PER_QUERY=10000
TIPG_CATALOG_TTL=300
TIPG_DB_SPATIAL_EXTENT=false
```
- `TIPG_DB_SPATIAL_EXTENT=false` — all geometries are NULL in Phase 2 (Pitfall #6)
- The `DATABASE_URL` template already exists at line 25 — fill in Docker defaults in the actual `.env`

---

### `apps/api/tests/test_structures.py` (test, request-response — NEW)

**Analog:** `apps/api/tests/test_provenance.py`

**Test class + mock helper pattern** (lines 19-36):
```python
class TestProvenanceEndpoints:
    """Tests for /api/v1/provenance CRUD endpoints."""

    def _mock_provenance(self, **overrides):
        """Create a mock ProvenanceModel instance."""
        defaults = {
            "id": uuid.uuid4(),
            "source_type": "kazvodhoz_spreadsheet",
            "source_reference": None,
            "confidence_level": "HIGH",
            "contributor": "ingest_pipeline",
            "recorded_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        mock = MagicMock()
        for key, val in defaults.items():
            setattr(mock, key, val)
        return mock
```

**Create endpoint test pattern** (lines 38-59):
```python
    def test_create_provenance(self, test_client):
        """POST /api/v1/provenance returns 201 with id, source_type, ..."""
        mock_prov = self._mock_provenance()
        with patch(
            "api.routes.provenance.create_provenance",
            AsyncMock(return_value=mock_prov),
        ):
            response = test_client.post(
                "/api/v1/provenance",
                json={
                    "source_type": "kazvodhoz_spreadsheet",
                    "confidence_level": "HIGH",
                    "contributor": "ingest_pipeline",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["source_type"] == "kazvodhoz_spreadsheet"
```

**404 test pattern** (lines 75-83):
```python
    def test_get_provenance_not_found(self, test_client):
        """GET /api/v1/provenance/{id} returns 404 for non-existent UUID."""
        non_existent_id = uuid.uuid4()
        with patch(
            "api.routes.provenance.get_provenance",
            AsyncMock(return_value=None),
        ):
            response = test_client.get(f"/api/v1/provenance/{non_existent_id}")
        assert response.status_code == 404
```

**Filter test pattern** (lines 85-99):
```python
    def test_query_provenance_by_source_type(self, test_client):
        """GET /api/v1/provenance?source_type=... returns filtered list."""
        mock_list = [self._mock_provenance(source_type="kazvodhoz_spreadsheet")]
        with patch(
            "api.routes.provenance.query_provenance",
            AsyncMock(return_value=mock_list),
        ):
            response = test_client.get(
                "/api/v1/provenance?source_type=kazvodhoz_spreadsheet"
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
```

**Integration test marker pattern** (lines 142-167):
```python
class TestProvenanceFKEnforcement:
    """Test that provenance_id FK is enforced (DATA-07)."""

    @pytest.mark.integration
    async def test_fact_has_provenance(self):
        """Creating a StructureFactModel without provenance_id raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError
        from api.infrastructure.database import async_session
        from api.models.structure import StructureFactModel

        fact = StructureFactModel(
            structure_id=uuid.uuid4(),
            attribute_name="condition",
            attribute_value={"value": "good"},
        )
        with pytest.raises(IntegrityError):
            async with async_session() as session:
                async with session.begin():
                    session.add(fact)
```

**What to copy for test_structures.py:**
- `_mock_structure(self, **overrides)` helper — id, name_ru, type, district, geometry=None, etc.
- `TestStructureEndpoints` class with:
  - `test_create_structure` — POST /api/v1/structures → 201
  - `test_get_structure` — GET /structures/{id} → 200
  - `test_get_structure_not_found` — GET /structures/{id} → 404
  - `test_list_structures` — GET /structures → list with total count
  - `test_list_with_filter` — GET /structures?type=canal&district=Район+1
  - `test_list_pagination` — GET /structures?offset=10&limit=20
  - `test_search` — GET /structures/search?q=канал&lang=ru
  - `test_fuzzy_search` — GET /structures/search?q=канал+42 (partial match)
  - `test_bbox_filter` — GET /structures?bbox=... (integration marker)
- Patch service functions: `api.routes.structures.create_structure`, `api.routes.structures.get_structure`, etc.
- Use `test_client` fixture from conftest.py

---

### `apps/api/tests/test_ingestion.py` (test, batch — NEW)

**Analog:** `apps/api/tests/test_provenance.py` (test structure) + RESEARCH.md test patterns

> **No existing Celery task test exists.** Follow the test class structure and mock patterns from test_provenance.py, but test the ingestion_service functions directly (unit tests) rather than through the API.

**What to create:**
- `TestIngestionParsing` class:
  - `test_parse_kazvodhoz_sheet` — verify row parsing skips headers/summaries
  - `test_cell_type_handling` — verify float-to-int conversion for years (Pitfall #1)
  - `test_skip_group_headers` — verify "Категория объектов" rows are skipped (Pitfall #2)
  - `test_skip_summary_rows` — verify aggregate totals are excluded
  - `test_cross_sheet_enrichment` — verify filterable columns from 'каналы' and 'Лист1' are merged (Pitfall #3)
- `TestIngestionIdempotency` class:
  - `test_idempotent_skip` — existing source_reference → skip
  - `test_force_reingest` — force=True → update existing
- `TestIngestionProvenance` class:
  - `test_provenance_creation` — each structure gets a ProvenanceModel with correct fields (D-20)
- Mock xlrd sheet data using `MagicMock` with `cell_value` and `nrows` attributes
- For bulk insert tests, mock `create_engine` + `Session` or use `@pytest.mark.integration` with Docker stack

---

### `apps/api/tests/test_tipg.py` (test, request-response integration — NEW)

**Analog:** `apps/api/tests/test_provenance.py` (integration marker pattern)

**Integration test marker pattern** (from `test_provenance.py` line 145):
```python
    @pytest.mark.integration
    async def test_fact_has_provenance(self):
        ...
```

**What to create:**
- `TestTiPGIntegration` class — all tests `@pytest.mark.integration`
  - `test_ogc_collection_exists` — GET http://localhost:8080/collections, assert `public.structures` in collections
  - `test_cql2_filter` — GET /collections/public.structures/items?filter=type='canal'&filter-lang=cql2-text
  - `test_items_geojson` — GET /collections/public.structures/items, assert GeoJSON FeatureCollection
  - `test_tilejson_endpoint` — GET /collections/public.structures/tiles/WebMercatorQuad/tilejson.json
  - `test_null_geometry_handling` — verify items with NULL geometry return `"geometry": null`
- Use `httpx.AsyncClient` for TiPG requests (TiPG runs on port 8080, separate from FastAPI on 8000)
- These tests require the full Docker stack running — use `@pytest.mark.integration`

---

### `apps/api/tests/conftest.py` (test config — MODIFY)

**Analog:** `apps/api/tests/conftest.py` (itself)

**Existing test_client fixture** (lines 96-108):
```python
@pytest.fixture
def test_client(mock_healthy_minio):
    """FastAPI TestClient with MinIO mocked for lifespan."""
    with patch("api.services.minio_client.Minio", mock_healthy_minio):
        from api.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            yield client
```

**sys.path setup pattern** (lines 9-10):
```python
sys.path.append(str(Path(__file__).parent.parent / "src"))
```

**What to add to conftest.py:**
- Add `mock_structure` fixture — returns a MagicMock simulating StructureModel with filterable columns
- Add `mock_structure_list` fixture — returns list of mock structures for pagination tests
- Add `mock_search_results` fixture — returns list of (model, score) tuples for search tests
- Add `mock_xlrd_sheet` fixture — returns a MagicMock simulating an xlrd Sheet with `cell_value`, `nrows`, `ncols` for ingestion tests
- The existing `test_client` fixture already patches MinIO for lifespan — new routes (structures, ingestion) will work with this fixture as-is since they don't require MinIO

---

## Shared Patterns

### Async Database Session (Service Layer)
**Source:** `apps/api/src/api/infrastructure/database.py` (lines 36-42) + `apps/api/src/api/services/provenance_service.py` (lines 41-42)
**Apply to:** `structure_service.py` — all CRUD operations
```python
# database.py — session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# provenance_service.py — usage pattern
async with async_session() as session:
    async with session.begin():
        model = Model(...)
        session.add(model)
        await session.flush()
        await session.refresh(model)
        return model
```

### Sync Database Session (Celery/Bulk)
**Source:** `apps/api/src/api/config/settings.py` (line 34) — `sync_database_url` already defined
**Apply to:** `ingestion_service.py` — bulk insert operations
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from api.config.settings import settings

engine = create_engine(settings.sync_database_url)
with Session(engine) as session:
    # bulk operations
    session.commit()
engine.dispose()
```

### Pydantic Response Models
**Source:** `apps/api/src/api/routes/provenance.py` (lines 48-58)
**Apply to:** All route files (structures.py, ingestion.py) + schemas/structures.py
```python
class ResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # fields...
```

### HTTPException 404 Pattern
**Source:** `apps/api/src/api/routes/provenance.py` (lines 84-88)
**Apply to:** `structures.py` — GET by ID endpoint
```python
if model is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Structure '{structure_id}' not found",
    )
```

### Global Exception Handler
**Source:** `apps/api/src/api/main.py` (lines 63-82)
**Apply to:** All new routes — inherited automatically, no action needed
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    logger.exception("unhandled_exception", ...)
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
```

### Structlog Logging
**Source:** `apps/api/src/api/services/provenance_service.py` (line 21)
**Apply to:** `structure_service.py`, `ingestion_service.py`, `celery_tasks.py` (modified)
```python
import structlog
logger = structlog.get_logger(__name__)
```

### Test Mock Pattern (patch service, assert HTTP)
**Source:** `apps/api/tests/test_provenance.py` (lines 41-44, 53-58)
**Apply to:** `test_structures.py` — all endpoint tests
```python
with patch(
    "api.routes.provenance.create_provenance",
    AsyncMock(return_value=mock_prov),
):
    response = test_client.post("/api/v1/provenance", json={...})
assert response.status_code == 201
```

### Docker Service Pattern (healthcheck + depends_on)
**Source:** `docker-compose.yml` (lines 61-87)
**Apply to:** TiPG service addition
```yaml
  tipg:
    image: ghcr.io/developmentseed/tipg:latest
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz.html"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 15s
```

### Alembic Raw SQL for PostGIS
**Source:** `apps/api/alembic/versions/0001_initial.py` (lines 64-67)
**Apply to:** `0002` migration — nullable geometry, generated tsvector, GIN/GiST indexes
```python
op.execute("CREATE INDEX ... USING GIST (geometry)")
op.execute("ALTER TABLE structures ALTER COLUMN geometry DROP NOT NULL")
op.execute("""ALTER TABLE structures ADD COLUMN search_ts_ru tsvector GENERATED ALWAYS AS (...) STORED""")
```

---

## No Analog Found

| File | Role | Data Flow | Reason | Fallback |
|------|------|-----------|--------|----------|
| `apps/api/src/api/schemas/structures.py` | schema | request-response | No `schemas/` directory exists. Provenance route defines Pydantic models inline. | Use inline Pydantic models in route (matching provenance pattern) OR create new `schemas/` dir (RESEARCH.md recommendation). Pattern to copy is the inline Pydantic class definitions from `provenance.py` lines 27-58. |
| `apps/api/src/api/services/ingestion_service.py` (sync/bulk portion) | service | batch | No existing sync or bulk-insert service. All services use async SQLAlchemy. | RESEARCH.md Pattern 4 (lines 366-463) provides complete sync psycopg + xlrd + bulk insert implementation. |
| `apps/api/src/api/routes/ingestion.py` (file upload + Celery trigger) | route | request-response (async) | No existing file upload or Celery task trigger route. | FastAPI `UploadFile` + `task.delay()` pattern. RESEARCH.md D-15 + FastAPI docs. |
| `apps/api/tests/test_ingestion.py` (xlrd parsing tests) | test | batch | No existing test for spreadsheet parsing or Celery tasks. | RESEARCH.md test patterns (lines 953-956). Mock xlrd sheet with MagicMock. |
| `apps/api/tests/test_tipg.py` (TiPG integration) | test | request-response (integration) | No existing integration test for external services. | RESEARCH.md test patterns (lines 961-962). httpx.AsyncClient to TiPG port 8080. `@pytest.mark.integration` marker. |

---

## Metadata

**Analog search scope:**
- `apps/api/src/api/routes/` — all route files (provenance.py, health.py, minio.py, __init__.py)
- `apps/api/src/api/services/` — provenance_service.py
- `apps/api/src/api/models/` — structure.py, provenance.py
- `apps/api/src/api/infrastructure/` — database.py
- `apps/api/src/api/config/` — settings.py
- `apps/api/src/api/tasks/` — celery_tasks.py
- `apps/api/src/api/` — celery_app.py, main.py
- `apps/api/alembic/versions/` — 0001_initial.py
- `apps/api/tests/` — conftest.py, test_provenance.py, test_schema.py, test_minio.py, test_health.py
- `docker-compose.yml`
- `docker/postgres/init-extensions.sql`
- `.env.example`

**Files scanned:** 18 source files + 2 planning documents (CONTEXT.md, RESEARCH.md)
**Pattern extraction date:** 2026-06-26
**Key finding:** pg_trgm extension is already enabled in `init-extensions.sql` (line 8) — no infrastructure change needed for trigram fuzzy search. The `sync_database_url` is already defined in settings.py (line 34) — no config change needed for Celery bulk insert.
