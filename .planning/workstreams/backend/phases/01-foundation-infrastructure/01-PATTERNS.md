# Phase 1: Foundation & Infrastructure - Pattern Map

**Mapped:** 2026-06-25
**Files analyzed:** 30 (new/modified files from RESEARCH.md recommended structure)
**Analogs found:** 21 / 30

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `docker-compose.yml` | config | service-orchestration | (none — new) | no analog |
| `docker/postgres/Dockerfile` | config | file-I/O | (none — new) | no analog |
| `docker/postgres/init-extensions.sql` | config | file-I/O | (none — new) | no analog |
| `apps/api/Dockerfile` | config | file-I/O | `apps/agent/Dockerfile` | exact |
| `apps/api/pyproject.toml` | config | n/a | `apps/agent/pyproject.toml` | exact |
| `.env` | config | n/a | `.env` (existing, modify) | exact (update) |
| `.env.example` | config | n/a | `.env.example` (existing) | exact (update) |
| `.env.remote` | config | n/a | (none — new) | no analog |
| `apps/api/src/api/config/__init__.py` | config | n/a | `apps/agent/src/agent/config/__init__.py` | exact |
| `apps/api/src/api/config/settings.py` | config | n/a | `apps/agent/src/agent/config/settings.py` | exact |
| `apps/api/src/api/infrastructure/__init__.py` | utility | n/a | `apps/agent/src/agent/utils/__init__.py` | role-match |
| `apps/api/src/api/infrastructure/database.py` | infrastructure | request-response | `apps/agent/src/agent/infrastructure/database.py` | exact |
| `apps/api/src/api/models/__init__.py` | model | n/a | `apps/agent/src/agent/config/__init__.py` | role-match |
| `apps/api/src/api/models/provenance.py` | model | CRUD | `apps/agent/src/agent/infrastructure/database.py` | role-match |
| `apps/api/src/api/models/structure.py` | model | CRUD | `apps/agent/src/agent/infrastructure/database.py` | role-match |
| `apps/api/src/api/routes/health.py` | route | request-response | `apps/agent/src/agent/routes/health.py` | exact |
| `apps/api/src/api/routes/provenance.py` | route | CRUD | `apps/agent/src/agent/routes/agent.py` | role-match |
| `apps/api/src/api/routes/minio.py` | route | request-response | `apps/agent/src/agent/routes/agent.py` | role-match |
| `apps/api/src/api/routes/__init__.py` | route | n/a | `apps/agent/src/agent/routes/__init__.py` | exact |
| `apps/api/src/api/services/minio_client.py` | service | file-I/O | (none — new) | no analog |
| `apps/api/src/api/services/provenance_service.py` | service | CRUD | `apps/agent/src/agent/infrastructure/thread_ownership.py` | role-match |
| `apps/api/src/api/services/__init__.py` | service | n/a | `apps/agent/src/agent/config/__init__.py` | role-match |
| `apps/api/src/api/tasks/__init__.py` | task | n/a | `apps/agent/src/agent/config/__init__.py` | role-match |
| `apps/api/src/api/tasks/celery_tasks.py` | task | event-driven | (none — new) | no analog |
| `apps/api/src/api/celery_app.py` | config | event-driven | (none — new) | no analog |
| `apps/api/src/api/utils/__init__.py` | utility | n/a | `apps/agent/src/agent/utils/__init__.py` | exact |
| `apps/api/src/api/utils/logging.py` | utility | n/a | `apps/agent/src/agent/utils/logging.py` | exact |
| `apps/api/src/api/main.py` | entry-point | request-response | `apps/agent/src/agent/server.py` | role-match |
| `apps/api/alembic/env.py` | migration | file-I/O | (none — new) | no analog |
| `apps/api/alembic.ini` | migration | file-I/O | (none — new) | no analog |
| `apps/api/alembic/versions/0001_initial.py` | migration | transform | (none — new) | no analog |
| `apps/api/tests/conftest.py` | test | n/a | `apps/agent/tests/conftest.py` | exact |
| `apps/api/tests/test_health.py` | test | request-response | `apps/agent/tests/test_api.py` | role-match |
| `apps/api/tests/test_provenance.py` | test | CRUD | `apps/agent/tests/test_api.py` | role-match |
| `apps/api/tests/test_minio.py` | test | request-response | `apps/agent/tests/test_api.py` | role-match |
| `apps/api/tests/test_schema.py` | test | CRUD | (none — new) | no analog |

---

## Pattern Assignments

### `apps/api/src/api/config/settings.py` (config)

**Analog:** `apps/agent/src/agent/config/settings.py`

**Imports pattern** (lines 1-3):
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv
```

**Core pattern — Pydantic Settings with env_prefix** (lines 5-38):
```python
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="API_",  # Changed from "AGENT_" to "API_"
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"
    debug: bool = True
```

**CRITICAL deviation from analog:** The agent's `settings.py` hardcodes remote alem.ai credentials as defaults (lines 97-108). The new API MUST use local Docker service defaults instead (per RESEARCH.md Anti-Pattern #6):
```python
# Database (local Docker defaults, NOT remote alem.ai)
database_url: str = "postgresql+asyncpg://sujoly:sujoly_dev@postgres:5432/sujoly"
sync_database_url: str = "postgresql://sujoly:sujoly_dev@postgres:5432/sujoly"
redis_url: str = "redis://redis:6379/0"
minio_endpoint: str = "minio:9000"
minio_access_key: str = "minioadmin"
minio_secret_key: str = "minioadmin"
minio_bucket: str = "sujoly-documents"
minio_use_ssl: bool = False
allowed_origins: str = "http://localhost:3000"
```

**Settings instantiation** (line 151):
```python
settings = Settings()
```

---

### `apps/api/src/api/infrastructure/database.py` (infrastructure, request-response)

**Analog:** `apps/agent/src/agent/infrastructure/database.py`

**Imports pattern** (lines 1-9):
```python
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, JSON, Uuid
from datetime import datetime
import uuid

from agent.config.settings import settings  # → from api.config.settings import settings
```

**asyncpg SSL compatibility pattern** (lines 25-37) — CRITICAL, prevents Pitfall #4:
```python
# Handle asyncpg SSL compatibility - asyncpg doesn't understand sslmode parameter
# Parse it out and convert to connect_args
_db_url = settings.database_url
_connect_args = {}
if "sslmode=disable" in _db_url:
    _db_url = _db_url.replace("?sslmode=disable", "").replace("&sslmode=disable", "")
    _connect_args["ssl"] = None

engine = create_async_engine(
    _db_url,
    echo=settings.debug,
    connect_args=_connect_args,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

**Session dependency pattern** (lines 42-44):
```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

**CRITICAL deviation from analog:** The agent uses `Base.metadata.create_all` for table creation (lines 47-50). The new API MUST use Alembic migrations instead (per RESEARCH.md Anti-Pattern #5). Do NOT include `init_db()` with `create_all`. Remove or replace with a comment pointing to Alembic.

**Base declaration** (line 11):
```python
Base = declarative_base()
```

---

### `apps/api/src/api/models/provenance.py` (model, CRUD)

**Analog:** `apps/agent/src/agent/infrastructure/database.py` (DocumentModel, lines 14-22)

**ORM model pattern** (lines 14-22 of analog):
```python
class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column("metadata", JSON, nullable=True)
```

**Recommended pattern for new API** — use SQLAlchemy 2.0 `Mapped` type hints (per RESEARCH.md Pattern 1, lines 223-288). The agent uses legacy `Column()` style; the new API should use the modern `mapped_column` approach:
```python
from sqlalchemy import String, Text, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid
from api.infrastructure.database import Base

class ProvenanceModel(Base):
    __tablename__ = "provenance"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(10), nullable=False, default="HIGH")
    contributor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
```

**See RESEARCH.md lines 223-288 for full ProvenanceModel, StructureModel, and StructureFactModel schema.** The research provides the complete schema with all columns, foreign keys, and the `Geometry("Point", srid=4326)` type from GeoAlchemy2.

---

### `apps/api/src/api/models/structure.py` (model, CRUD)

**Analog:** `apps/agent/src/agent/infrastructure/database.py` (DocumentModel pattern)

Same ORM model pattern as provenance above, but with GeoAlchemy2 spatial types. **No existing analog for Geometry types** — this is new to the project. Follow RESEARCH.md Pattern 1 (lines 242-262) for the full StructureModel with:
```python
from geoalchemy2 import Geometry
geometry = mapped_column(Geometry("Point", srid=4326), nullable=False)
```

And StructureFactModel with JSONB (lines 265-288):
```python
from sqlalchemy.dialects.postgresql import JSONB
attribute_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
```

---

### `apps/api/src/api/routes/health.py` (route, request-response)

**Analog:** `apps/agent/src/agent/routes/health.py`

**Imports pattern** (lines 1-18 of analog):
```python
import time
import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel

from agent.config.settings import settings  # → from api.config.settings import settings

router = APIRouter(tags=["health"])
logger = structlog.get_logger(__name__)
```

**Health response models** (lines 37-48 of analog) — reuse this Pydantic model pattern:
```python
class ComponentHealth(BaseModel):
    status: Literal["ok", "error"]
    message: str | None = None

class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    checks: dict[str, ComponentHealth]
```

**Deep health check pattern** (lines 70-119 of analog) — the agent checks LLM + Milvus. The new API checks PostgreSQL + Redis + MinIO instead. Follow the same try/except structure:
```python
@router.get("/health/ready", response_model=HealthStatus)
async def readiness_check() -> HealthStatus:
    checks: dict[str, ComponentHealth] = {}
    overall: Literal["healthy", "degraded", "unhealthy"] = "healthy"

    # Check PostgreSQL
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            checks["postgres"] = ComponentHealth(status="ok")
    except Exception as e:
        checks["postgres"] = ComponentHealth(status="error", message=str(e))
        overall = "degraded"

    # Check Redis, MinIO similarly...
    return HealthStatus(status=overall, checks=checks)
```

**See RESEARCH.md lines 629-686 for the complete `/health` endpoint implementation** with DB, Redis, and MinIO probes.

**Simple liveness check** (lines 64-67 of analog):
```python
@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    return {"status": "ok"}
```

---

### `apps/api/src/api/routes/provenance.py` (route, CRUD)

**Analog:** `apps/agent/src/agent/routes/agent.py`

**Router declaration pattern** (line 16 of analog):
```python
router = APIRouter(prefix="/api/v1", tags=["api-v1"])
logger = structlog.get_logger(__name__)
```

**Request/response model pattern** (lines 20-62 of analog) — Pydantic BaseModel with Field validation:
```python
class ChatMessage(BaseModel):
    type: str = Field(..., description="Message type: human or assistant")
    content: str = Field(..., min_length=1, max_length=32000, description="Message content")
```

**Endpoint pattern with error handling** (lines 185-193 of analog):
```python
@router.get("/models/{model_id}", response_model=ModelInfo)
async def get_model_info(request: Request, model_id: str):
    if model_id not in ALEM_MODELS:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found. Available: {list(ALEM_MODELS.keys())}",
        )
    return model_to_info(model_id)
```

**Apply to provenance endpoints:**
- `POST /api/v1/provenance` — create provenance record (validate body, call service, return 201)
- `GET /api/v1/provenance/{id}` — retrieve by UUID
- `GET /api/v1/provenance` — query by source_type, confidence, timestamp (SC-2)

---

### `apps/api/src/api/routes/minio.py` (route, request-response)

**Analog:** `apps/agent/src/agent/routes/agent.py` (router pattern)

Same router declaration and Pydantic model pattern as provenance route above. Endpoints:
- `POST /api/v1/minio/presign` — generate presigned upload URL
- `GET /api/v1/minio/presign/{object_name}` — generate presigned download URL

Access MinIO service via `request.app.state.minio` (set in lifespan, see main.py pattern below).

---

### `apps/api/src/api/services/provenance_service.py` (service, CRUD)

**Analog:** `apps/agent/src/agent/infrastructure/thread_ownership.py`

This analog is a service-like module with async DB operations. Follow its pattern.

**Imports pattern** (lines 1-7 of analog):
```python
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.infrastructure.database import Base, async_session  # → api.infrastructure.database

logger = structlog.get_logger(__name__)
```

**Async DB operation pattern** (lines 20-33 of analog) — create with idempotent check:
```python
async def ensure_thread_ownership(thread_id: str, user_id: str) -> None:
    try:
        async with async_session() as session:
            async with session.begin():
                existing = await session.execute(
                    select(ThreadOwnership).where(
                        ThreadOwnership.thread_id == thread_id
                    )
                )
                if not existing.scalar_one_or_none():
                    session.add(
                        ThreadOwnership(thread_id=thread_id, user_id=user_id)
                    )
    except Exception:
        logger.warning("operation_failed", exc_info=True)
```

**Query pattern** (lines 43-54 of analog):
```python
async def check_thread_access(thread_id: str, user_id: str) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(ThreadOwnership).where(
                ThreadOwnership.thread_id == thread_id
            )
        )
        record = result.scalar_one_or_none()
        return record is not None
```

Apply to provenance_service: `create_provenance()`, `get_provenance()`, `query_provenance()` (filter by source_type, confidence, timestamp).

---

### `apps/api/src/api/main.py` (entry-point, request-response)

**Analog:** `apps/agent/src/agent/server.py`

**Imports pattern** (lines 1-29 of analog):
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import time

from agent.config.settings import settings  # → from api.config.settings import settings
from agent.utils.logging import configure_logging  # → from api.utils.logging import configure_logging
from agent.infrastructure.database import engine, Base  # → from api.infrastructure.database import engine
from agent.routes import health, agent  # → from api.routes import health, provenance, minio
```

**Lifespan pattern** (lines 32-40 of analog):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services
    # Agent does: async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    # NEW API: Don't use create_all. Instead, init MinIO client + ensure buckets.
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
```

**See RESEARCH.md lines 435-468 for the complete lifespan implementation.**

**App creation pattern** (lines 46-53 of analog):
```python
configure_logging(level="DEBUG" if settings.debug else "INFO")

app = FastAPI(
    title="SuJoly Inspector API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)
```

**Global exception handler** (lines 59-81 of analog) — reuse exactly:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import structlog
    logger = structlog.get_logger(__name__)

    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    logger.exception(
        "unhandled_exception",
        request_id=getattr(request.state, "request_id", "unknown"),
        path=request.url.path,
        error_type=type(exc).__name__,
    )
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
```

**Route registration** (lines 149-151 of analog):
```python
app.include_router(health.router)
app.include_router(provenance.router)
app.include_router(minio.router)
```

---

### `apps/api/src/api/utils/logging.py` (utility)

**Analog:** `apps/agent/src/agent/utils/logging.py` (52 lines — copy nearly verbatim)

**Complete file** — this is the exact pattern to follow. The entire file (lines 1-52):
```python
"""Logging configuration."""

import logging
import sys
import structlog
from pythonjsonlogger import jsonlogger

def configure_logging(level: str = "INFO"):
    root_log = logging.getLogger()
    root_log.setLevel(level)

    for handler in root_log.handlers[:]:
        root_log.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if not sys.stdout.isatty():
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "timestamp"}
        )
        handler.setFormatter(formatter)

    root_log.addHandler(handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if sys.stdout.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    return structlog.get_logger(name)
```

**Note:** The agent's `pyproject.toml` includes `python-json-logger>=2.0.7` as a dependency. The new API's `pyproject.toml` must also include it, OR use structlog's built-in JSON rendering (the `structlog.processors.JSONRenderer()` already handles JSON in non-TTY mode). Consider dropping `pythonjsonlogger` if the stdlib handler isn't needed separately.

---

### `apps/api/src/api/utils/__init__.py` (utility, barrel export)

**Analog:** `apps/agent/src/agent/utils/__init__.py` (6 lines)

```python
"""Logging utility."""

from agent.utils.logging import configure_logging, get_logger  # → api.utils.logging

__all__ = ["configure_logging", "get_logger"]
```

Drop `configure_observability` and `get_tracer` (OpenTelemetry) — not needed for Phase 1.

---

### `apps/api/Dockerfile` (config, file-I/O)

**Analog:** `apps/agent/Dockerfile` (42 lines)

**Multi-stage uv build pattern** (lines 1-16 of analog):
```dockerfile
# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml ./

ENV UV_HTTP_TIMEOUT=300
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project --index-strategy unsafe-best-match

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
```

**Runtime stage** (lines 18-42 of analog):
```dockerfile
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data/uploads && \
    chown -R appuser:appuser /app/data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Changes for new API:**
- `CMD` → `["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]`
- Remove `ENV UV_EXTRA_INDEX_URL` (no PyTorch in API)
- Remove `:/app/src/agent/gen` from PYTHONPATH (no protobuf gen)
- Drop the `UV_EXTRA_INDEX_URL` line (line 9 of analog — PyTorch CPU index not needed)

---

### `apps/api/pyproject.toml` (config)

**Analog:** `apps/agent/pyproject.toml` (69 lines)

**Project metadata pattern** (lines 1-6 of analog):
```toml
[project]
name = "api"
version = "0.1.0"
description = "SuJoly Inspector — Backend API for hydraulic structures catalog"
requires-python = ">=3.12"
dependencies = [
    # Core: fastapi, uvicorn, sqlalchemy, geoalchemy2, asyncpg, alembic
    # Tasks: celery, redis
    # Storage: minio, pgvector
    # Config: pydantic-settings, structlog, python-dotenv
    # Uploads: python-multipart
    # Sync driver for Alembic: psycopg[binary,pool]
]
```

**See RESEARCH.md lines 78-86 for exact `uv add` commands and dependency list.**

**pytest config** (lines 47-49 of analog) — copy exactly:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Package layout** (lines 65-69 of analog):
```toml
[tool.setuptools.package-dir]
"" = "src"

[tool.setuptools.packages.find]
where = ["src"]
```

**Dev dependencies** (lines 60-63 of analog):
```toml
[dependency-groups]
dev = [
    "ruff>=0.14.10",
]
```
Add: `pytest`, `pytest-asyncio`, `httpx` (or put in main deps like the agent does).

**Entry points** (lines 51-54 of analog):
```toml
[project.scripts]
api-server = "api.main:main"
```

---

### `apps/api/tests/conftest.py` (test)

**Analog:** `apps/agent/tests/conftest.py` (19 lines)

**Path setup pattern** (lines 1-9 of analog):
```python
"""Test configuration."""

import pytest
import sys
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))
```

**Mock fixture pattern** (lines 12-19 of analog):
```python
@pytest.fixture
def mock_vector_store():
    with pytest.MonkeyPatch.context() as m:
        mock_store = MagicMock()
        m.setattr("agent.tools.retrieval.get_vector_store", lambda: mock_store)
        yield mock_store
```

**For the new API, add fixtures for:**
- `async_db_session` — async test DB session (use `httpx.AsyncClient` + test engine)
- `mock_minio` — mock MinIO client for presigned URL tests
- `test_client` — FastAPI TestClient with mocked dependencies

---

### `apps/api/tests/test_health.py` (test, request-response)

**Analog:** `apps/agent/tests/test_api.py`

**TestClient pattern** (lines 42-61 of analog):
```python
@pytest.fixture
def app_with_mock_agent(mock_agent):
    with patch("agent.core.agent.Agent") as MockAgent:
        mock_instance = MagicMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_agent)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        MockAgent.return_value = mock_instance

        from agent.server import app
        app.state.agent = mock_agent
        yield app


class TestHealthEndpoints:
    def test_health_check(self, app_with_mock_agent):
        client = TestClient(app_with_mock_agent)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

**Apply to health tests:**
- `test_health_live` — `GET /health/live` returns 200 `{"status": "ok"}`
- `test_health_ready_all_healthy` — mock DB, Redis, MinIO as healthy → 200
- `test_health_ready_db_down` — mock DB failure → 503 with `checks["postgres"]["status"] == "error"`
- `test_health_ready_redis_down` — similar
- `test_health_ready_minio_down` — similar

**Async test pattern** (from `apps/agent/tests/test_server_auth.py`, lines 15-19):
```python
@pytest.mark.asyncio
async def test_get_current_user_dev_mode_without_keys():
    user = await get_current_user(api_key=None, credentials=None)
    assert user.user_id == "dev-user"
```

---

### `apps/api/tests/test_provenance.py` (test, CRUD)

**Analog:** `apps/agent/tests/test_api.py` (TestClient + class-based test grouping)

Follow the same class-based test structure (lines 56-168 of analog):
```python
class TestProvenanceEndpoints:
    def test_create_provenance(self, test_client):
        response = test_client.post("/api/v1/provenance", json={...})
        assert response.status_code == 201

    def test_get_provenance(self, test_client):
        response = test_client.get("/api/v1/provenance/{id}")
        assert response.status_code == 200

    def test_query_by_source(self, test_client):
        response = test_client.get("/api/v1/provenance?source_type=kazvodhoz_spreadsheet")
        assert response.status_code == 200
```

---

### `apps/api/tests/test_minio.py` (test, request-response)

**Analog:** `apps/agent/tests/test_api.py` (TestClient pattern)

Mock MinIO service in `app.state.minio` and test:
- `test_presigned_upload_url` — POST returns URL string
- `test_presigned_download_url` — GET returns URL string
- `test_presigned_roundtrip` — SC-3 integration test

---

### `apps/api/src/api/config/__init__.py` (config, barrel export)

**Analog:** `apps/agent/src/agent/config/__init__.py` (1 line)

```python
"""Configuration and settings."""
```

Simple docstring-only `__init__.py` pattern. No exports needed — settings accessed via `from api.config.settings import settings`.

---

### `apps/api/src/api/routes/__init__.py` (route, barrel export)

**Analog:** `apps/agent/src/agent/routes/__init__.py` (empty file)

The agent's `routes/__init__.py` is empty. Follow the same — routes are imported directly in `main.py` via `from api.routes import health, provenance, minio`.

---

## Shared Patterns

### Security Headers Middleware
**Source:** `apps/agent/src/agent/server.py` lines 84-137
**Apply to:** `apps/api/src/api/main.py` — all HTTP responses

```python
@app.middleware("http")
async def add_headers_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception:
        raise

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'"

    return response
```

**Drop from analog:** The agent's middleware includes admin route API key auth (lines 92-113) and metrics auth (lines 104-113). Phase 1 has no auth — skip those blocks. Keep only the request ID, timing, and security headers.

### CORS Middleware
**Source:** `apps/agent/src/agent/server.py` lines 140-147
**Apply to:** `apps/api/src/api/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-User-ID", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)
```

### Structured Logging
**Source:** `apps/agent/src/agent/utils/logging.py` (full file)
**Apply to:** All modules in `apps/api/src/api/`

```python
from api.utils import get_logger
logger = get_logger(__name__)
logger.info("event_name", key="value")  # structlog context
```

Configuration is called once at app startup:
```python
configure_logging(level="DEBUG" if settings.debug else "INFO")
```

### Settings Access
**Source:** `apps/agent/src/agent/config/settings.py` line 151
**Apply to:** All modules needing config

```python
from api.config.settings import settings
settings.database_url  # Pydantic-validated, API_ prefix
```

### Database Session Access
**Source:** `apps/agent/src/agent/infrastructure/database.py` lines 39-44
**Apply to:** All services and routes needing DB access

```python
from api.infrastructure.database import async_session, get_session

# Pattern 1: direct session (services)
async with async_session() as session:
    async with session.begin():
        session.add(model)

# Pattern 2: dependency injection (routes)
@router.get("/items")
async def list_items(session: AsyncSession = Depends(get_session)):
    ...
```

### Global Exception Handler
**Source:** `apps/agent/src/agent/server.py` lines 59-81
**Apply to:** `apps/api/src/api/main.py` — catches all unhandled exceptions

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    logger.exception("unhandled_exception", ...)
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
```

### Docker Multi-Stage Build
**Source:** `apps/agent/Dockerfile`
**Apply to:** `apps/api/Dockerfile`

Two-stage build: `uv:python3.12-bookworm-slim` builder → `python:3.12-slim-bookworm` runtime. Copy `.venv` and `src` from builder. Non-root user (`appuser`). HEALTHCHECK with curl.

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason | Reference |
|------|------|-----------|--------|-----------|
| `docker-compose.yml` | config | service-orchestration | No Docker Compose file exists in the project | RESEARCH.md lines 329-428 (complete YAML) |
| `docker/postgres/Dockerfile` | config | file-I/O | No custom Postgres Dockerfile exists | RESEARCH.md lines 601-615 (complete Dockerfile) |
| `docker/postgres/init-extensions.sql` | config | file-I/O | No SQL init scripts exist | RESEARCH.md lines 618-625 (complete SQL) |
| `.env.remote` | config | n/a | No remote env file exists; create from existing `.env` remote values | RESEARCH.md lines 200-203 |
| `apps/api/src/api/services/minio_client.py` | service | file-I/O | No MinIO service class exists in agent | RESEARCH.md lines 300-322 (complete class) |
| `apps/api/src/api/celery_app.py` | config | event-driven | No Celery app exists in agent | RESEARCH.md lines 688-714 (complete module) |
| `apps/api/src/api/tasks/celery_tasks.py` | task | event-driven | No Celery tasks exist in agent | RESEARCH.md lines 709-713 (health_check_task) |
| `apps/api/alembic/env.py` | migration | file-I/O | Agent uses `create_all`, not Alembic | RESEARCH.md lines 476-490 (GeoAlchemy2 helpers) |
| `apps/api/alembic.ini` | migration | file-I/O | No Alembic config exists | Standard Alembic template + RESEARCH.md |
| `apps/api/alembic/versions/0001_initial.py` | migration | transform | No migrations exist | RESEARCH.md Pattern 1 (lines 213-288) for schema |
| `apps/api/tests/test_schema.py` | test | CRUD | No schema validation tests exist in agent | RESEARCH.md lines 831-835 (test map) |

---

## Key Pattern Differences: Agent vs New API

| Aspect | Agent (`apps/agent/`) | New API (`apps/api/`) | Why |
|--------|----------------------|----------------------|-----|
| Env prefix | `AGENT_` | `API_` | Namespace isolation |
| Settings defaults | Hardcoded remote alem.ai creds | Local Docker service creds | RESEARCH.md Anti-Pattern #6 |
| Schema creation | `Base.metadata.create_all` | Alembic migrations | RESEARCH.md Anti-Pattern #5 |
| ORM column style | Legacy `Column()` | Modern `Mapped` + `mapped_column` | SQLAlchemy 2.0 best practice |
| Spatial types | None | GeoAlchemy2 `Geometry` | PostGIS requirement |
| Background tasks | None (in-process) | Celery + Redis broker | Durable, retryable tasks |
| Object storage | MinIO settings only, no service class | MinIOService with presigned URLs | INT-04 requirement |
| Vector search | Milvus (pymilvus) | pgvector (PostgreSQL extension) | STACK.md decision |
| Auth | Kratos session (server_auth.py) | None (Phase 1), RBAC in Phase 3 | RESEARCH.md Security Domain |
| Rate limiting | SlowAPI | None (Phase 1) | Not needed for foundation |
| Observability | OpenTelemetry | None (Phase 1) | Not needed for foundation |

---

## Metadata

**Analog search scope:** `apps/agent/src/agent/` (all Python files), `apps/agent/tests/`, `apps/agent/Dockerfile`, `apps/agent/pyproject.toml`, `.env.example`, `.gitignore`
**Files scanned:** 15 analog files read in full
**Pattern extraction date:** 2026-06-25
