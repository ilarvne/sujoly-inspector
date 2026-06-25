# Phase 1: Foundation & Infrastructure - Research

**Researched:** 2026-06-25
**Domain:** Docker infrastructure, PostGIS schema design, provenance tracking, FastAPI skeleton, MinIO object storage
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-07 | Every fact and status on every structure has a provenance record (source type, source reference, confidence level, timestamp, contributor) | Provenance schema design pattern with dedicated `provenance` table + FK references from all fact tables. See Architecture Patterns > Provenance Tracking Pattern. |
| INT-04 | System separates imagery evidence (STAC/COG in MinIO) from structure features (PostGIS) per the architecture principle | MinIO bucket structure for asset types, PostGIS schema for vector features only. Binary assets never stored in PostGIS. See Architecture Patterns > Architecture Separation. |
</phase_requirements>

## Summary

Phase 1 establishes the full Docker Compose stack (PostgreSQL/PostGIS/pgvector, Redis, MinIO, FastAPI, Celery) with a PostGIS schema that includes provenance tracking on all structure records, and a clear architectural separation between vector features (PostGIS) and binary assets (MinIO). This is a greenfield backend phase — no existing backend API code exists, though a RAG agent app at `apps/agent/` provides reference patterns (Pydantic Settings, SQLAlchemy 2.0 async, structlog, FastAPI lifespan, security headers middleware).

The critical technical challenge is that `postgis/postgis:17-3.5` does NOT include pgvector by default. However, `postgresql-17-pgvector` IS available via the PGDG apt repository already configured in the image [VERIFIED: Docker runtime test]. A custom Dockerfile extending `postgis/postgis:17-3.5` with a single `apt-get install postgresql-17-pgvector` line solves this cleanly.

The project has remote infrastructure already provisioned at alem.ai (PostgreSQL, MinIO, Redis). The success criteria requires a single Docker Compose command for all services. The research recommends building a **fully local Docker Compose stack** for development — the remote services are for deployment/demo, not for the developer's local stack. The local `.env` should use local Docker service credentials, not the remote alem.ai credentials.

**Primary recommendation:** Build a custom `postgis-pgvector` Docker image, a `docker-compose.yml` with health-checked services and `depends_on: condition: service_healthy`, an Alembic migration creating the provenance schema, and a FastAPI app with `/health` endpoint that verifies all service connectivity. This Walking Skeleton proves the architecture in one command.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Structure feature storage | Database / Storage (PostGIS) | — | PostGIS is the system of record for all structure vector data. Spatial queries, GiST indexes, ST_AsMVT all happen here. |
| Provenance tracking | Database / Storage (PostgreSQL) | API / Backend | Provenance records are relational data — source, confidence, timestamp. The API writes them; PostgreSQL stores and queries them. |
| Binary asset storage (imagery, documents, photos) | CDN / Static (MinIO) | API / Backend | MinIO is S3-compatible object storage. Binary assets never touch PostGIS. The API generates presigned URLs for upload/download. |
| Health check orchestration | API / Backend (FastAPI) | — | FastAPI's `/health` endpoint aggregates DB, Redis, and MinIO connectivity status. Celery worker health is separate. |
| Background task execution | API / Backend (Celery) | Database / Storage (Redis) | Celery workers process background jobs. Redis is the message broker and result backend. |
| Configuration management | API / Backend (Pydantic Settings) | — | All service connection info flows through typed Pydantic Settings loaded from env vars. No hardcoded URLs. |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.138.1 | Async Python API framework | Latest stable. High performance, automatic OpenAPI docs, type-hint validation. Lifespan context managers for startup/shutdown. [VERIFIED: PyPI] |
| uvicorn | 0.49.0 | ASGI server | Standard FastAPI server. Use with `--host 0.0.0.0 --port 8000` in Docker. [VERIFIED: PyPI] |
| SQLAlchemy | 2.0.51 | Async ORM, database abstraction | 2.0 has native async support (AsyncSession, async_engine). Declarative with Mapped type hints. [VERIFIED: PyPI] |
| GeoAlchemy2 | 0.20.0 | PostGIS spatial types for SQLAlchemy | Adds Geometry, Geography types. Spatial functions via `func.ST_*`. Alembic-compatible via `alembic_helpers`. [VERIFIED: PyPI] |
| asyncpg | 0.31.0 | Async PostgreSQL driver | Fastest Python PostgreSQL driver. SQLAlchemy async backend (`postgresql+asyncpg://`). [VERIFIED: PyPI] |
| Alembic | 1.18.5 | Database migrations | Standard SQLAlchemy migration tool. GeoAlchemy2 provides `alembic_helpers` for spatial index creation. [VERIFIED: PyPI] |
| Celery | 5.6.3 | Distributed task queue | Battle-tested, mature ecosystem. Handles OCR, ingestion, tile pre-generation. Redis broker. [VERIFIED: PyPI] |
| redis | 8.0.1 | Redis Python client | Celery broker/result backend, API response cache. [VERIFIED: PyPI] |
| minio | 7.2.20 | MinIO S3-compatible client | Presigned URLs, bucket operations, object upload/download. [VERIFIED: PyPI] |
| pgvector | 0.4.2 | pgvector Python adapter | SQLAlchemy Vector type support for pgvector extension. [VERIFIED: PyPI] |
| Pydantic Settings | 2.14.2 | Configuration management | Environment-based config with type validation. Pairs with FastAPI. [VERIFIED: PyPI] |
| structlog | 26.1.0 | Structured logging | JSON logging in production. Already used in existing agent app — follow established pattern. [VERIFIED: PyPI] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | latest | File upload handling | Required by FastAPI for `UploadFile` — MinIO presigned URL workflow |
| psycopg[binary] | latest | Sync PostgreSQL driver | Alembic migrations use sync connections. Also useful for Celery tasks. [VERIFIED: existing agent pyproject.toml] |
| httpx | latest | Async HTTP client | Health check probes to MinIO, testing API endpoints. [VERIFIED: existing agent pyproject.toml] |
| pytest | latest | Test framework | Unit + integration tests. pytest-asyncio for async test support. [VERIFIED: existing agent pyproject.toml] |
| pytest-asyncio | latest | Async test support | `asyncio_mode = "auto"` — follow existing agent pattern. [VERIFIED: existing agent pyproject.toml] |
| ruff | latest | Linter/formatter | Already in agent dev deps. Use for all backend code. [VERIFIED: existing agent pyproject.toml] |
| python-dotenv | latest | .env file loading | Load environment variables from `.env` file. [VERIFIED: existing agent pyproject.toml] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom postgis-pgvector Dockerfile | `datosonline/postgis-pgvector:latest` | Pre-built image saves a Dockerfile but adds external dependency on an unofficial image. Custom Dockerfile is 2 lines and fully reproducible. |
| Custom postgis-pgvector Dockerfile | `pgvector/pgvector:pg17` + install PostGIS | Reverses the dependency — more complex. PostGIS has more apt dependencies. Better to start from PostGIS image and add pgvector. |
| Celery | Taskiq | Modern async-first alternative. Viable but smaller ecosystem. Celery is proven and the STACK.md already chose it. |
| MinIO Python SDK | boto3 | boto3 is the AWS SDK, works with MinIO but heavier. MinIO SDK is purpose-built, lighter, has `presigned_get_object`/`presigned_put_object` helpers. |

**Installation:**
```bash
# Backend API (apps/api/) — using uv per project convention
uv init apps/api --python 3.12
cd apps/api
uv add fastapi uvicorn sqlalchemy geoalchemy2 asyncpg alembic celery redis minio pgvector pydantic-settings structlog python-multipart python-dotenv
uv add --dev pytest pytest-asyncio httpx ruff
# psycopg for sync Alembic migrations
uv add "psycopg[binary,pool]"
```

**Version verification (PyPI, 2026-06-25):**
```
fastapi==0.138.1    celery==5.6.3     minio==7.2.20
uvicorn==0.49.0     redis==8.0.1      pgvector==0.4.2
sqlalchemy==2.0.51  structlog==26.1.0 pydantic-settings==2.14.2
geoalchemy2==0.20.0 asyncpg==0.31.0  alembic==1.18.5
```

## Package Legitimacy Audit

> slopcheck v0.6.1 ran successfully. All packages verified [OK] on PyPI.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| fastapi | PyPI | ~6 yrs | ~50M/mo | github.com/fastapi/fastapi | [OK] | Approved |
| uvicorn | PyPI | ~8 yrs | ~40M/mo | github.com/encode/uvicorn | [OK] | Approved |
| sqlalchemy | PyPI | ~18 yrs | ~80M/mo | github.com/sqlalchemy/sqlalchemy | [OK] | Approved |
| geoalchemy2 | PyPI | ~13 yrs | ~2M/mo | github.com/geoalchemy/geoalchemy2 | [OK] | Approved |
| asyncpg | PyPI | ~8 yrs | ~20M/mo | github.com/MagicStack/asyncpg | [OK] | Approved |
| alembic | PyPI | ~12 yrs | ~30M/mo | github.com/sqlalchemy/alembic | [OK] | Approved |
| celery | PyPI | ~16 yrs | ~15M/mo | github.com/celery/celery | [OK] | Approved |
| redis | PyPI | ~14 yrs | ~25M/mo | github.com/redis/redis-py | [OK] | Approved |
| minio | PyPI | ~9 yrs | ~3M/mo | github.com/minio/minio-py | [OK] | Approved |
| pgvector | PyPI | ~3 yrs | ~2M/mo | github.com/pgvector/pgvector-python | [OK] | Approved |
| pydantic-settings | PyPI | ~3 yrs | ~30M/mo | github.com/pydantic/pydantic-settings | [OK] | Approved |
| structlog | PyPI | ~11 yrs | ~10M/mo | github.com/hynek/structlog | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                    docker compose up
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │PostgreSQL│   │  Redis   │   │  MinIO   │
   │+PostGIS  │   │  7-alpine│   │  latest  │
   │+pgvector │   │          │   │          │
   │:5432     │   │  :6379   │   │:9000/9001│
   └────┬─────┘   └────┬─────┘   └────┬─────┘
        │              │              │
        │    ┌─────────┴─────────┐    │
        │    │                   │    │
        ▼    ▼                   │    │
   ┌──────────────┐         ┌────┴────┴───┐
   │   FastAPI    │         │   Celery    │
   │   :8000      │         │   Worker    │
   │              │         │             │
   │ /health ─────┼─────────┤ async tasks │
   │ /provenance  │         │ health task │
   │ /minio/*     │         │             │
   └──────────────┘         └─────────────┘
        │                        │
        │  Health Check Flow:    │
        │  /health → DB conn?   │
        │  /health → Redis ping?│
        │  /health → MinIO ok?  │
        │                        │
        ▼                        ▼
   provenance table          celery beat
   structures table          task queue
   (PostGIS geometry)        (Redis broker)
```

**Data flow for Walking Skeleton:**
1. `docker compose up` starts all 5 services with health checks
2. PostgreSQL init script creates `postgis`, `vector`, `pg_trgm` extensions
3. Alembic migration creates `provenance` + `structures` tables
4. FastAPI lifespan connects to DB, creates MinIO bucket if missing
5. `/health` endpoint checks DB connectivity + Redis ping + MinIO bucket existence
6. `/provenance` endpoint creates/retrieves provenance records (proves DATA-07)
7. `/minio/presign` endpoint generates presigned URLs (proves MinIO works)
8. Celery worker processes `health_check_task` (proves Celery + Redis work)

### Recommended Project Structure

```
.
├── docker-compose.yml          # All 5 services + health checks
├── docker/
│   └── postgres/
│       ├── Dockerfile          # FROM postgis/postgis:17-3.5 + pgvector
│       └── init-extensions.sql # CREATE EXTENSION postgis, vector, pg_trgm
├── apps/
│   ├── agent/                  # Existing RAG agent (unchanged)
│   └── api/                    # New FastAPI backend
│       ├── src/
│       │   └── api/
│       │       ├── config/         # Pydantic Settings (env prefix: API_)
│       │       ├── infrastructure/ # SQLAlchemy async engine, Base, session
│       │       ├── models/         # ORM models (provenance, structures)
│       │       ├── routes/         # FastAPI routers (health, provenance, minio)
│       │       ├── services/       # Business logic (minio_client, provenance_service)
│       │       ├── tasks/          # Celery task definitions
│       │       ├── utils/          # Logging (structlog), health checks
│       │       ├── celery_app.py   # Celery instance (Redis broker)
│       │       └── main.py         # FastAPI app — lifespan, middleware, routes
│       ├── alembic/
│       │   ├── env.py              # Configured with geoalchemy2.alembic_helpers
│       │   └── versions/           # Migration scripts
│       ├── alembic.ini
│       ├── tests/
│       │   ├── conftest.py         # Shared fixtures (async DB session, MinIO mock)
│       │   ├── test_health.py      # Health endpoint integration tests
│       │   ├── test_provenance.py  # Provenance CRUD tests
│       │   └── test_minio.py       # Presigned URL tests
│       ├── pyproject.toml
│       └── Dockerfile              # Multi-stage: uv builder + slim runtime
├── .env                        # Local Docker credentials (NOT remote alem.ai)
├── .env.example                # Template with local defaults
└── .env.remote                 # Remote alem.ai credentials (for deployment)
```

### Pattern 1: Provenance Tracking (DATA-07)
**What:** Every fact and status on every structure carries an immutable provenance record identifying where the data came from, how confident we are, when it was recorded, and who contributed it.
**When to use:** Always — this is a core architecture principle, not an optional feature.

The provenance pattern uses a dedicated `provenance` table that all fact tables reference via foreign key. This normalizes provenance metadata and makes it queryable.

**Example:**
```python
# Source: Research design based on row-level provenance pattern
# [CITED: medium.com/towards-data-engineering/row-level-provenance]

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Uuid, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

class ProvenanceModel(Base):
    """Immutable record of where a fact came from."""
    __tablename__ = "provenance"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # source_type values: 'kazvodhoz_spreadsheet', 'osm', 'satellite', 'ocr',
    #                     'manual', 'ai_inferred', 'inspection'
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    # URL, file path, OSM element ID, satellite scene ID, etc.
    confidence_level: Mapped[str] = mapped_column(String(10), nullable=False, default="HIGH")
    # HIGH, MEDIUM, LOW — enum constraint recommended
    contributor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Person, system, or process that contributed this fact
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )


class StructureModel(Base):
    """Canonical structure record — one per hydraulic structure."""
    __tablename__ = "structures"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name_ru: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name_kk: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    geometry = mapped_column(Geometry("Point", srid=4326), nullable=False)
    # Provenance for the structure's existence itself
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class StructureFactModel(Base):
    """Time-based facts about a structure with provenance.
    Every attribute (condition, capacity, length, etc.) is a separate
    fact with its own provenance and time validity range.
    """
    __tablename__ = "structure_facts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    structure_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("structures.id"), nullable=False, index=True
    )
    attribute_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 'condition', 'capacity_m3s', 'length_km', 'wear_percent', etc.
    attribute_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    provenance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("provenance.id"), nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True  # NULL = currently valid
    )
```

### Pattern 2: Architecture Separation (INT-04)
**What:** Structure features (vector data) live in PostGIS. Binary assets (satellite imagery, documents, photos) live in MinIO. PostGIS stores references to MinIO objects, never the binary data itself.
**When to use:** Always — this is a locked architecture principle.

**MinIO bucket structure:**
- `sujoly-imagery` — COGs, satellite scenes, water index composites (STAC items)
- `sujoly-documents` — Scanned passports, inspection reports, spreadsheets
- `sujoly-photos` — Field inspection photos, voice note attachments

**Example:**
```python
# Source: MinIO Python SDK official docs [CITED: github.com/minio/minio-py]

from minio import Minio
from datetime import timedelta

class MinIOService:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool):
        self.client = Minio(endpoint, access_key=access_key,
                           secret_key=secret_key, secure=secure)

    def ensure_bucket(self, bucket_name: str) -> None:
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def presigned_upload_url(self, bucket: str, object_name: str,
                             expires: timedelta = timedelta(hours=1)) -> str:
        return self.client.presigned_put_object(bucket, object_name, expires=expires)

    def presigned_download_url(self, bucket: str, object_name: str,
                               expires: timedelta = timedelta(hours=2)) -> str:
        return self.client.presigned_get_object(bucket, object_name, expires=expires)
```

### Pattern 3: Docker Compose with Health-Checked Services
**What:** All services have health checks. Application services use `depends_on: condition: service_healthy` to wait for infrastructure readiness.
**When to use:** Always in Docker Compose — prevents race conditions on startup.

**Example:**
```yaml
# Source: Docker Compose official docs [CITED: docs.docker.com/compose/how-tos/startup-order]
# + MinIO health check from official repo [CITED: github.com/minio/minio]

services:
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
      # Check extensions are installed, not just pg_isready
      # PostGIS init script restarts DB — pg_isready returns true prematurely
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB && psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c \"SELECT extname FROM pg_extension WHERE extname='postgis';\" | grep postgis"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-minioadmin}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data
    healthcheck:
      # Use mc ready local, NOT curl — curl was removed from recent MinIO images
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./apps/api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-sujoly}:${POSTGRES_PASSWORD:-sujoly_dev}@postgres:5432/${POSTGRES_DB:-sujoly}
      REDIS_URL: redis://redis:6379/0
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY:-minioadmin}
      MINIO_BUCKET: sujoly-documents
      MINIO_USE_SSL: "false"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 20s

  celery-worker:
    build:
      context: ./apps/api
    command: celery -A api.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-sujoly}:${POSTGRES_PASSWORD:-sujoly_dev}@postgres:5432/${POSTGRES_DB:-sujoly}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  pgdata:
  redisdata:
  miniodata:
```

### Pattern 4: FastAPI Lifespan with Service Initialization
**What:** Use `@asynccontextmanager` lifespan to initialize DB engine, MinIO client, and ensure buckets exist on startup. Clean up on shutdown.
**When to use:** Always — replaces deprecated `startup`/`shutdown` events.

**Example:**
```python
# Source: FastAPI official docs [CITED: fastapi.github.io/fastapi/advanced/events]

from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.infrastructure.database import init_db, engine
from api.services.minio_client import MinIOService
from api.config.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services
    minio = MinIOService(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl,
    )
    for bucket in ["sujoly-imagery", "sujoly-documents", "sujoly-photos"]:
        minio.ensure_bucket(bucket)
    app.state.minio = minio

    yield

    # Shutdown: clean up
    await engine.dispose()


app = FastAPI(
    title="SuJoly Inspector API",
    version="0.1.0",
    lifespan=lifespan,
)
```

### Pattern 5: Alembic with GeoAlchemy2 Helpers
**What:** Alembic autogenerate produces broken migrations for GeoAlchemy2 spatial types. Use `alembic_helpers` to fix this.
**When to use:** Always when using GeoAlchemy2 with Alembic.

**Example:**
```python
# Source: GeoAlchemy2 official docs [CITED: geoalchemy-2.readthedocs.io/en/latest/alembic.html]

# alembic/env.py
from geoalchemy2 import alembic_helpers

def run_migrations_online():
    # ...
    context.configure(
        # ...
        include_object=alembic_helpers.include_object,
        process_revision_directives=alembic_helpers.writer,
        render_item=alembic_helpers.render_item,
    )
```

### Anti-Patterns to Avoid

- **Storing binary data in PostGIS:** Never store images, COGs, or documents in PostgreSQL bytea columns. Use MinIO. PostGIS is for vector features and spatial metadata only.
- **Using `pg_isready` alone for PostGIS health check:** The PostGIS Docker image restarts the database during extension initialization. `pg_isready` returns true before extensions are ready. Always check for extension availability in the health check. [CITED: github.com/postgis/docker-postgis/issues/296]
- **Using `curl` for MinIO health check:** Recent MinIO Docker images removed `curl` from the base image. Use `mc ready local` instead. [CITED: github.com/minio/minio/issues/18389]
- **Using `depends_on` without `condition: service_healthy`:** Plain `depends_on` only controls start order, not readiness. Application services will race-condition against infrastructure startup. [CITED: docs.docker.com/compose/how-tos/startup-order]
- **Hardcoding remote service credentials in settings defaults:** The existing agent app has hardcoded alem.ai credentials in `settings.py` defaults. The new API should use env vars with local Docker defaults, not remote credentials.
- **Using `create_all` instead of Alembic migrations:** The existing agent app uses `Base.metadata.create_all` for table creation. The new API must use Alembic migrations for schema versioning and reproducibility.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PostGIS+pgvector Docker image | Custom multi-extension install script | Custom Dockerfile: `FROM postgis/postgis:17-3.5` + `apt-get install postgresql-17-pgvector` | 2-line Dockerfile. PGDG apt repo already configured in base image. [VERIFIED: Docker runtime test] |
| Presigned URL generation | Custom HMAC-SHA1 signing | `minio.presigned_get_object()` / `presigned_put_object()` | S3 signature v4 protocol is complex. MinIO SDK handles it. [CITED: github.com/minio/minio-py] |
| Spatial index creation in migrations | Manual `CREATE INDEX ... USING gist` SQL | GeoAlchemy2 `Geometry(spatial_index=True)` + `alembic_helpers` | Autogenerate produces correct GiST index. `alembic_helpers` fixes import issues. [CITED: geoalchemy-2.readthedocs.io] |
| Health check aggregation | Custom polling loop | FastAPI `/health` endpoint with DB/Redis/MinIO probes | Standard pattern. Returns 503 if any service unhealthy. |
| Celery task queue | Custom asyncio background tasks | Celery 5.6.3 with Redis broker | Durable, retryable, monitorable. FastAPI BackgroundTasks are in-process only — not durable. |
| Configuration management | Custom env var parsing | Pydantic Settings with typed fields | Type validation, defaults, env file loading. Already used in agent app. |
| Structured logging | Custom JSON formatter | structlog with JSON renderer | Battle-tested. Already used in agent app. Follow established pattern. |

**Key insight:** The existing `apps/agent/` codebase already solves several of these problems (Pydantic Settings, structlog, SQLAlchemy async, FastAPI lifespan). Follow those patterns, don't reinvent them.

## Runtime State Inventory

> This is a greenfield phase. No existing backend state to migrate.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — new database, no existing records | N/A — fresh schema creation |
| Live service config | None — no existing backend API running | N/A — new service deployment |
| OS-registered state | None — no OS-level registrations | N/A |
| Secrets/env vars | `.env` has remote alem.ai credentials (PostgreSQL, MinIO, Redis). These are for deployment, NOT local dev. | Create local `.env` with Docker service credentials. Keep remote credentials in `.env.remote` for deployment. |
| Build artifacts | `apps/agent/.venv/` — existing agent virtualenv. Unrelated to new API. | N/A — new API gets its own venv at `apps/api/.venv/` |

**Note:** The existing `apps/agent/` codebase is separate from this phase. The agent has its own database table (`documents`) in the shared remote PostgreSQL. The new API will use a local PostgreSQL instance. No conflict.

## Common Pitfalls

### Pitfall 1: PostGIS Health Check Race Condition
**What goes wrong:** `pg_isready` returns true before PostGIS extensions are fully installed. The PostGIS Docker init script restarts the database after installing extensions. Application services that depend on `service_healthy` may connect before extensions are ready.
**Why it happens:** The `postgis/postgis` Docker image runs `/docker-entrypoint-initdb.d/10_postgis.sh` which creates extensions, then reconnects. `pg_isready` only checks if the server accepts connections, not if extensions are loaded.
**How to avoid:** Use a health check that verifies extension availability:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB && psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c \"SELECT extname FROM pg_extension WHERE extname='postgis';\" | grep postgis"]
  start_period: 30s
```
**Warning signs:** Application starts, connects to DB, then fails with "extension postgis does not exist" errors.

### Pitfall 2: MinIO curl Health Check Failure
**What goes wrong:** Using `curl -f http://localhost:9000/minio/health/live` as MinIO health check fails because recent MinIO Docker images (ubi-micro base) don't include `curl`.
**Why it happens:** MinIO switched to a minimal base image that strips `curl`.
**How to avoid:** Use `mc ready local` — the `mc` binary is bundled in the MinIO image. [CITED: github.com/minio/minio/issues/18389]
**Warning signs:** MinIO container shows "executable file not found" in health check logs.

### Pitfall 3: pgvector Not in postgis/postgis Image
**What goes wrong:** `CREATE EXTENSION vector` fails with "control file not found" because pgvector is not installed in the `postgis/postgis:17-3.5` image.
**Why it happens:** The official PostGIS Docker image includes PostGIS extensions only, not pgvector.
**How to avoid:** Build a custom Dockerfile:
```dockerfile
FROM postgis/postgis:17-3.5
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-17-pgvector && rm -rf /var/lib/apt/lists/*
```
The `postgresql-17-pgvector` package IS available via the PGDG apt repository already configured in the base image. [VERIFIED: Docker runtime test — `apt-cache search pgvector` inside `postgis/postgis:17-3.5` after `apt-get update`]
**Warning signs:** `CREATE EXTENSION vector` fails on container startup.

### Pitfall 4: asyncpg SSL Mode Incompatibility
**What goes wrong:** SQLAlchemy async engine with asyncpg fails when `sslmode=disable` is in the connection URL. asyncpg doesn't understand the `sslmode` parameter.
**Why it happens:** asyncpg uses a different SSL configuration mechanism than psycopg2.
**How to avoid:** Strip `sslmode` from the URL and pass `ssl` via `connect_args`. The existing agent app already handles this:
```python
_connect_args = {}
if "sslmode=disable" in _db_url:
    _db_url = _db_url.replace("?sslmode=disable", "").replace("&sslmode=disable", "")
    _connect_args["ssl"] = None
engine = create_async_engine(_db_url, connect_args=_connect_args)
```
**Warning signs:** Connection errors mentioning "sslmode" parameter when connecting to local Docker PostgreSQL.

### Pitfall 5: Alembic Autogenerate Breaks with GeoAlchemy2
**What goes wrong:** `alembic revision --autogenerate` produces migration scripts with missing `geoalchemy2` imports and duplicate GiST index creation.
**Why it happens:** Alembic's autogenerate doesn't understand GeoAlchemy2's spatial types and index creation by default.
**How to avoid:** Configure `alembic/env.py` with `geoalchemy2.alembic_helpers`:
```python
from geoalchemy2 import alembic_helpers
context.configure(
    include_object=alembic_helpers.include_object,
    process_revision_directives=alembic_helpers.writer,
    render_item=alembic_helpers.render_item,
)
```
**Warning signs:** Migration scripts fail with `NameError: name 'geoalchemy2' is not defined` or duplicate index errors.

### Pitfall 6: Hardcoded Remote Credentials in Settings Defaults
**What goes wrong:** The existing agent app's `settings.py` has hardcoded remote alem.ai credentials as defaults. If the new API follows this pattern, local Docker development breaks when the remote services are unreachable.
**Why it happens:** The agent was built to connect to provisioned remote infrastructure.
**How to avoid:** The new API's settings should use LOCAL Docker service defaults:
```python
database_url: str = "postgresql+asyncpg://sujoly:sujoly_dev@postgres:5432/sujoly"
redis_url: str = "redis://redis:6379/0"
minio_endpoint: str = "minio:9000"
```
Remote credentials should come from `.env` or `.env.remote` only, never as defaults.
**Warning signs:** API fails to connect on `docker compose up` because it's trying to reach `a1-postgres1.alem.ai`.

## Code Examples

### Custom PostGIS+pgvector Dockerfile
```dockerfile
# Source: Research — verified via Docker runtime test
# [VERIFIED: apt-cache search pgvector inside postgis/postgis:17-3.5]

FROM postgis/postgis:17-3.5

# Install pgvector extension from PGDG apt repository
# (PGDG repo is already configured in the base postgres image)
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-17-pgvector && \
    rm -rf /var/lib/apt/lists/*

# init-extensions.sql is copied via docker-compose volume mount
# or COPY into /docker-entrypoint-initdb.d/
```

### Init Extensions Script
```sql
-- Source: PostGIS Docker docs [CITED: hub.docker.com/r/postgis/postgis]
-- + pgvector installation docs [CITED: github.com/pgvector/pgvector]

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- pg_trgm is needed for Phase 2 fuzzy matching, install now to avoid migration later
```

### FastAPI Health Check Endpoint
```python
# Source: Research design based on FastAPI + SQLAlchemy patterns

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from minio import Minio

router = APIRouter()

@router.get("/health")
async def health_check():
    """Aggregate health check — verifies DB, Redis, and MinIO connectivity."""
    checks = {}
    all_healthy = True

    # Check PostgreSQL
    try:
        from api.infrastructure.database import async_session
        async with async_session() as session:  # type: AsyncSession
            result = await session.execute(text("SELECT 1"))
            checks["postgres"] = "healthy"
    except Exception as e:
        checks["postgres"] = f"unhealthy: {e}"
        all_healthy = False

    # Check Redis
    try:
        from api.config.settings import settings
        redis = Redis.from_url(settings.redis_url)
        await redis.ping()
        await redis.aclose()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"
        all_healthy = False

    # Check MinIO
    try:
        from api.config.settings import settings
        minio = Minio(settings.minio_endpoint,
                      access_key=settings.minio_access_key,
                      secret_key=settings.minio_secret_key,
                      secure=settings.minio_use_ssl)
        minio.bucket_exists(settings.minio_bucket)
        checks["minio"] = "healthy"
    except Exception as e:
        checks["minio"] = f"unhealthy: {e}"
        all_healthy = False

    status_code = 200 if all_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "healthy" if all_healthy else "degraded", "checks": checks}
    )
```

### Celery App with Redis Broker
```python
# Source: Celery official docs [CITED: docs.celeryq.dev/en/stable]

from celery import Celery
from api.config.settings import settings

celery_app = Celery(
    "sujoly_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def health_check_task():
    """Simple task to verify Celery + Redis are working."""
    from datetime import datetime, timezone
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
```

### Pydantic Settings for the API
```python
# Source: Existing agent pattern + Pydantic Settings docs
# [CITED: github.com/agent/config/settings.py] + [CITED: pydantic-settings docs]

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"
    debug: bool = True

    # Database (local Docker defaults, NOT remote alem.ai)
    database_url: str = "postgresql+asyncpg://sujoly:sujoly_dev@postgres:5432/sujoly"
    # Sync URL for Alembic migrations
    sync_database_url: str = "postgresql://sujoly:sujoly_dev@postgres:5432/sujoly"

    # Redis (local Docker default)
    redis_url: str = "redis://redis:6379/0"

    # MinIO (local Docker defaults)
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "sujoly-documents"
    minio_use_ssl: bool = False

    # CORS
    allowed_origins: str = "http://localhost:3000"

settings = Settings()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` | `@asynccontextmanager` lifespan | FastAPI 0.93 (2023) | Single function for startup+shutdown. Cleaner resource management. |
| `next-pwa` for PWA | Serwist (`@serwist/next`) | Next.js PWA docs update | Turbopack-compatible. next-pwa is webpack-only. (Frontend phase) |
| psycopg2 for Alembic | psycopg3 (`psycopg[binary]`) | psycopg3 release | Async-capable, modern API. Still use sync mode for Alembic. |
| `create_all` for schema | Alembic migrations | Always (best practice) | Version-controlled, reversible schema changes. |
| Milvus for vector search | pgvector for small-to-medium scale | pgvector 0.7+ | No separate infrastructure. Hybrid search in SQL. [CITED: STACK.md] |

**Deprecated/outdated:**
- `@app.on_event("startup")` / `@app.on_event("shutdown")`: Replaced by lifespan context manager in FastAPI 0.93+.
- `curl` in MinIO health checks: Removed from recent MinIO Docker images. Use `mc ready local`.
- `postgres` volume path `/var/lib/postgresql/data`: Changed to `/var/lib/postgresql` in PostgreSQL 18+ images. Current project uses PG17, so old path is correct.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The remote alem.ai PostgreSQL does NOT have PostGIS/pgvector extensions installed | Environment Availability | If it does, could use remote DB for dev. But success criteria requires local Docker stack, so this doesn't change the plan. |
| A2 | `postgresql-17-pgvector` from PGDG apt works correctly with the postgis/postgis:17-3.5 base image | Standard Stack, Code Examples | If incompatible, need to build pgvector from source. Low risk — PGDG packages are tested with PG17. |
| A3 | The Celery worker should share the same Docker image as the FastAPI API | Architecture Patterns | If separate images needed, add a separate Dockerfile. Low risk — same codebase, different entrypoint. |
| A4 | `pg_trgm` extension should be installed in Phase 1 even though it's used in Phase 2 | Code Examples | If not installed now, Phase 2 needs a migration to add it. Minor — but installing now avoids a migration. |
| A5 | The new API app should be at `apps/api/` following the `apps/agent/` pattern | Project Structure | If a different location is preferred, adjust paths. Low impact. [ASSUMED — based on existing `apps/` directory convention] |

## Open Questions (RESOLVED)

1. **Local vs Remote Infrastructure**
   - What we know: `.env` has remote alem.ai credentials for PostgreSQL, MinIO, Redis. Success criteria says "single Docker Compose command" for all services.
   - What's unclear: Should the team use remote services for development, or local Docker? The success criteria strongly implies local Docker.
   - RESOLVED: Build local Docker Compose stack. Keep remote credentials in `.env.remote` for deployment. This satisfies the success criteria and gives full control over extensions (PostGIS, pgvector).

2. **Shared Database with Agent App**
   - What we know: The agent app at `apps/agent/` uses the remote PostgreSQL at alem.ai. The new API will use a local PostgreSQL in Docker.
   - What's unclear: Will the agent eventually need to query the API's local database, or will they always be separate?
   - RESOLVED: Keep them separate for Phase 1. The agent has its own `documents` table. The API has its own `provenance` and `structures` tables. Integration between agent and API happens in Phase 5 via REST endpoints.

3. **MinIO Bucket Creation Timing**
   - What we know: MinIO buckets need to exist before presigned URLs work. FastAPI lifespan can create them on startup.
   - What's unclear: Should bucket creation be in the FastAPI lifespan, in an init script, or in a Celery task?
   - RESOLVED: FastAPI lifespan — it's the simplest and runs once on startup. The `ensure_bucket` method is idempotent.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | All containerized services | ✓ | 29.4.1 | — |
| Docker Compose | Service orchestration | ✓ | 5.1.3 | — |
| Python 3.12 | FastAPI + Celery runtime | ✓ | 3.12.12 | — |
| uv | Python package management | ✓ | 0.11.8 | pip (slower, no lockfile) |
| Node.js | Frontend (not this phase) | ✓ | v24.14.1 | — |
| pg_isready | PostgreSQL health check | ✓ | 18.3 | In Docker image |
| curl | FastAPI health check | ✓ | 8.19.0 | In Docker image |
| redis-cli | Redis health check | ✗ | — | Available inside `redis:7-alpine` Docker image |
| Git | Version control | ✓ | (repo exists) | — |

**Missing dependencies with no fallback:** none — all required tools are available.
**Missing dependencies with fallback:** redis-cli is not installed on the host, but it's available inside the Docker container and used there for health checks.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]` with `asyncio_mode = "auto"`) |
| Quick run command | `cd apps/api && uv run pytest tests/ -x -v` |
| Full suite command | `cd apps/api && uv run pytest tests/ -v --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-07 | Provenance record can be created and retrieved with all fields | unit + integration | `uv run pytest tests/test_provenance.py -x` | ❌ Wave 0 |
| DATA-07 | Every structure fact references a provenance record | integration | `uv run pytest tests/test_provenance.py::test_fact_has_provenance -x` | ❌ Wave 0 |
| INT-04 | MinIO presigned URLs work for upload and download | integration | `uv run pytest tests/test_minio.py -x` | ❌ Wave 0 |
| INT-04 | Structure features stored in PostGIS, not MinIO | integration | `uv run pytest tests/test_schema.py::test_geometry_in_postgis -x` | ❌ Wave 0 |
| SC-1 | All Docker Compose services report healthy | smoke (manual) | `docker compose ps` — all services "healthy" | N/A |
| SC-2 | Provenance queryable by source, confidence, timestamp | integration | `uv run pytest tests/test_provenance.py::test_query_by_source -x` | ❌ Wave 0 |
| SC-3 | MinIO serves presigned URLs correctly | integration | `uv run pytest tests/test_minio.py::test_presigned_roundtrip -x` | ❌ Wave 0 |
| SC-4 | Architecture separation: imagery in MinIO, features in PostGIS | integration | `uv run pytest tests/test_schema.py::test_no_binary_in_postgis -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd apps/api && uv run pytest tests/ -x -v`
- **Per wave merge:** `cd apps/api && uv run pytest tests/ -v --tb=short` + `docker compose up -d && docker compose ps` (verify all healthy)
- **Phase gate:** Full suite green + all Docker services healthy before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `apps/api/tests/conftest.py` — shared fixtures (async DB session, test MinIO client, test client)
- [ ] `apps/api/tests/test_health.py` — health endpoint tests (DB, Redis, MinIO checks)
- [ ] `apps/api/tests/test_provenance.py` — provenance CRUD + query tests (DATA-07)
- [ ] `apps/api/tests/test_minio.py` — presigned URL roundtrip tests (INT-04, SC-3)
- [ ] `apps/api/tests/test_schema.py` — schema validation tests (INT-04, SC-4)
- [ ] Framework install: `uv add --dev pytest pytest-asyncio httpx` — if not present in initial `pyproject.toml`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (Phase 3) | N/A — auth (RBAC) is Phase 3 (RISK-07). Phase 1 has no auth. |
| V3 Session Management | no (Phase 3) | N/A — no sessions in Phase 1. |
| V4 Access Control | no (Phase 3) | N/A — no access control in Phase 1. |
| V5 Input Validation | yes | Pydantic v2 for all request/response models. Type-hint-based validation. |
| V6 Cryptography | yes | Secrets via env vars only. No hardcoded credentials. `.env` in `.gitignore`. |
| V7 Error Handling | yes | Global exception handler (follow agent app pattern). No stack traces in responses. |
| V8 Data Protection | yes | MinIO presigned URLs with expiry. No long-lived URLs. |
| V9 Communications | yes | Security headers middleware (follow agent app pattern — HSTS, X-Frame-Options, etc.) |
| V14 Configuration | yes | Pydantic Settings with env vars. Debug mode off in production. |

### Known Threat Patterns for FastAPI + PostgreSQL + MinIO Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection | Tampering | SQLAlchemy parameterized queries. Never raw SQL with string formatting. |
| Secrets in code | Information Disclosure | Pydantic Settings from env vars. `.env` in `.gitignore`. No hardcoded credentials in settings defaults. |
| Presigned URL abuse | Elevation of Privilege | Short expiry times (1-2 hours). Bucket-scoped permissions. |
| Container port exposure | Information Disclosure | Only expose necessary ports in Docker Compose. Internal services communicate via Docker network. |
| Debug mode in production | Information Disclosure | `debug: bool = True` default for dev only. Override via env var in production. |

### Security Headers (from existing agent app pattern)
```python
# Follow the pattern from apps/agent/src/agent/server.py
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
```

## Sources

### Primary (HIGH confidence)
- Context7 `/fastapi/fastapi` — lifespan context manager, SQL database patterns (2153 snippets)
- Context7 `/geoalchemy/geoalchemy2` — Geometry types, Alembic helpers, spatial index (987 snippets)
- Context7 `/minio/minio-py` — presigned URLs, bucket operations, put/get object (147 snippets)
- Context7 `/websites/celeryq_dev_en_stable` — Redis broker config, task definition, testing (4697 snippets)
- Docker runtime test — `apt-cache search pgvector` inside `postgis/postgis:17-3.5` confirmed `postgresql-17-pgvector` available via PGDG apt
- PyPI `pip index versions` — verified all 12 core packages exist with current versions
- slopcheck v0.6.1 — all 12 packages verified [OK], no hallucinated packages

### Secondary (MEDIUM confidence)
- Docker Hub `postgis/postgis` — image tags, extension list, volume path changes [CITED: hub.docker.com/r/postgis/postgis]
- Docker Compose docs — `depends_on` with `condition: service_healthy` [CITED: docs.docker.com/compose/how-tos/startup-order]
- MinIO GitHub issue #18389 — curl removed from image, use `mc ready local` [CITED: github.com/minio/minio/issues/18389]
- PostGIS Docker GitHub issue #296 — health check race condition during extension init [CITED: github.com/postgis/docker-postgis/issues/296]
- pgvector installation docs — apt, Docker, build from source methods [CITED: github.com/pgvector/pgvector]
- Debian package search — `postgresql-17-pgvector` available in trixie/sid [CITED: packages.debian.org]
- Row-level provenance pattern — three-column provenance triplet [CITED: medium.com/towards-data-engineering/row-level-provenance]
- Existing codebase — `apps/agent/` patterns (Pydantic Settings, SQLAlchemy async, structlog, security headers)

### Tertiary (LOW confidence)
- `datosonline/postgis-pgvector` Docker image — alternative pre-built image option [CITED: hub.docker.com/r/datosonline/postgis-pgvector]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified on PyPI + slopcheck [OK] + versions confirmed
- Architecture: HIGH — patterns verified via Context7 + official docs + existing codebase patterns
- Pitfalls: HIGH — 4 of 6 pitfalls verified via official GitHub issues + Docker runtime tests
- Docker setup: HIGH — pgvector availability confirmed via live Docker runtime test
- Provenance schema: MEDIUM — based on research patterns + project requirements, not a tested implementation

**Research date:** 2026-06-25
**Valid until:** 2026-07-25 (30 days — stable infrastructure stack, low churn)
