# Phase 1: Foundation & Infrastructure - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the foundational infrastructure layer: a Docker Compose stack with PostgreSQL/PostGIS/pgvector, Redis, MinIO, TiPG, TiTiler, FastAPI skeleton, and Celery worker. The database schema includes a `structures` table with PostGIS geometry and a polymorphic `provenance` table tracking source, confidence, and timestamp on every fact. MinIO is configured with pre-created buckets and presigned URL endpoints. Architecture separation between imagery evidence (MinIO) and structure features (PostGIS) is established at the storage level.

**In scope:** Docker Compose stack, database schema (structures + provenance), FastAPI app skeleton, MinIO bucket setup, health checks for all services, presigned URL endpoint.
**Out of scope:** Data ingestion (Phase 2), OGC API configuration (Phase 2), risk models (Phase 3), discovery algorithms (Phase 4), RAG agent integration (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Infrastructure Deployment Target
- **D-01:** Hybrid infrastructure — local Docker Compose for development with Alem-hosted infra as fallback via environment variables. The existing agent app already connects to Alem-hosted PostgreSQL, Redis, MinIO; the new API app should support both targets.
- **D-02:** Multi-file Docker Compose overlay structure: `docker-compose.yml` (base definitions) + `docker-compose.override.yml` (local dev defaults, auto-loaded) + `docker-compose.alem.yml` (Alem infra connections, used with `-f` flag). Clean separation, standard Docker Compose pattern.
- **D-03:** Include TiPG and TiTiler as containers in the Phase 1 Docker stack. They're part of the target architecture and including them now proves the full stack early. TiPG on port 8080, TiTiler on port 8081.
- **D-04:** Use `postgis/postgis:17-3.5` Docker image with pgvector extension installed manually via SQL (`CREATE EXTENSION vector`). Matches STACK.md recommendation. Single image, pgvector added at init time via init script.

### Project Structure & Dependencies
- **D-05:** FastAPI backend lives at `apps/api/` mirroring the `apps/agent/` pattern: own `pyproject.toml`, `src/` layout, `uv` for dependency management. Each app is independently buildable.
- **D-06:** Mirror the agent's established patterns: Pydantic Settings with `env_prefix` (e.g., `API_`), structlog for structured logging, OpenTelemetry for tracing, slowapi for rate limiting, multi-stage Dockerfile with `uv` builder. Consistent codebase style across apps.
- **D-07:** Database access via SQLAlchemy 2.0 async + GeoAlchemy2 + asyncpg + Alembic for migrations. Type-safe PostGIS queries, async-native, industry standard. Alembic manages all schema changes.
- **D-08:** Celery with Redis broker for background jobs. Include Celery worker container in Phase 1 Docker stack. Battle-tested, Flower monitoring, Beat scheduling. Handles future OCR, ingestion, tile pre-generation.

### Provenance Model Design
- **D-09:** Separate `provenance` table with FK relationship to entity records. Clean, queryable, supports full history. Standard relational pattern.
- **D-10:** Polymorphic design: `provenance` table has `entity_type` (enum: structure, inspection, document, etc.) + `entity_id` (UUID) columns. Single table for all provenance, one query for cross-entity provenance. No FK enforcement but application-layer validation.
- **D-11:** Each entity record has `current_provenance_id` FK pointing to the latest provenance entry. Provenance table retains full history. Fast "what's the source of this fact NOW" queries via FK; history via `SELECT * FROM provenance WHERE entity_type='structure' AND entity_id=X ORDER BY captured_at DESC`.
- **D-12:** Provenance table fields: `id` (UUID PK), `entity_type` (enum), `entity_id` (UUID), `source_type` (enum: spreadsheet, osm, satellite, ocr, manual, api), `source_reference` (text: file name, OSM node ID, scene ID, etc.), `confidence` (enum: HIGH, MEDIUM, LOW), `contributor` (text: user name or system), `captured_at` (timestamptz), `valid_from` (timestamptz), `valid_to` (timestamptz, nullable — null means current), `created_at` (timestamptz default now()).

### DB Schema Scope
- **D-13:** Minimal table creation in Phase 1: `structures` + `provenance` only. Later phases add their own tables (inspections, documents, candidates, risk_scores) via Alembic migrations. Clean walking skeleton.
- **D-14:** `structures` table includes core identity + geometry + status + Kazvodhoz spreadsheet columns: `id` (UUID PK), `name_ru`, `name_kk`, `name_en` (trilingual names), `structure_type`, `geometry` (PostGIS), `district`, `water_source`, `commissioning_year`, `technical_condition`, `wear_percentage`, `current_provenance_id` (FK to provenance), `status`, `condition_score`, `created_at`, `updated_at`. Phase 2 ingestion maps directly.
- **D-15:** Dual SRID storage: `geometry` column in QazTRF-23 (EPSG:10941) for coordinate accuracy + `geometry_4326` column in WGS84 for web display/API. Transform at ingest time (Phase 2). Both columns indexed with GiST. Preserves original coordinates and enables web-standard output.
- **D-16:** Pre-create MinIO buckets via init script: `sujoly-structures` (documents/photos), `sujoly-imagery` (STAC/COG), `sujoly-reports` (exports). Establishes INT-04 architecture separation at storage level. FastAPI has `/api/v1/files/presigned-url` endpoint to generate presigned URLs for upload/download.

### the agent's Discretion
- Docker Compose network configuration and volume naming conventions
- FastAPI app internal module structure (routers, models, schemas, services)
- Alembic migration directory structure and initial migration naming
- Celery task module organization (empty stubs for now)
- TiPG and TiTiler configuration file specifics
- Health check endpoint paths and response formats
- Docker Compose service naming conventions

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Environment & Configuration
- `.env.example` — Environment variable template with all connection strings (PostgreSQL, MinIO, Redis, Milvus, Alem LLM APIs). The API app should use a subset of these vars with `API_` prefix.
- `AGENTS.md` (STACK.md section) — Full technology stack with verified versions, rationale, and alternatives considered. Contains Docker Compose service table with ports.

### Existing Code Patterns to Mirror
- `apps/agent/pyproject.toml` — Dependency management pattern (uv, Python 3.12, pyproject.toml with src/ layout). Mirror this structure for apps/api/.
- `apps/agent/Dockerfile` — Multi-stage Dockerfile pattern (uv builder, python:3.12-slim runtime, healthcheck, non-root user). Mirror for apps/api/Dockerfile.
- `apps/agent/src/agent/config/settings.py` — Pydantic Settings pattern (BaseSettings, env_prefix, SettingsConfigDict). Mirror with `API_` prefix for the API app.

### Project Planning
- `.planning/workstreams/backend/REQUIREMENTS.md` — Backend requirements with traceability. Phase 1 covers DATA-07 and INT-04.
- `.planning/workstreams/backend/ROADMAP.md` — Phase dependencies and success criteria. Phase 1 is the foundation for all subsequent phases.
- `.planning/PROJECT.md` — Project context, key decisions, and constraints. Contains architecture principle: "Every structure has one canonical asset record, many evidence sources, and a time-based condition history."

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/agent/Dockerfile` — Multi-stage build pattern with uv cache mounts, non-root user, healthcheck. Copy this pattern for the API Dockerfile.
- `apps/agent/src/agent/config/settings.py` — Pydantic Settings class with env_prefix, Alem LLM model configs, infra connection strings. Reuse the pattern, not the values.
- `apps/agent/pyproject.toml` — uv + pyproject.toml + src/ layout convention. Follow for apps/api/.

### Established Patterns
- **Dependency management:** `uv` with `pyproject.toml`, `src/` layout, `uv sync --frozen`
- **Config:** Pydantic Settings with `env_prefix`, `.env` file loading via `python-dotenv`
- **Logging:** `structlog` for structured JSON logging
- **Tracing:** OpenTelemetry with FastAPI instrumentation
- **Rate limiting:** `slowapi` with per-user and global limits
- **Docker:** Multi-stage builds, `python:3.12-slim-bookworm` runtime, healthcheck via curl
- **Database:** `asyncpg` + `SQLAlchemy 2.0` async, `psycopg` for sync operations

### Integration Points
- `.env.example` at repo root defines all environment variables — the API app reads a subset
- Agent app connects to same PostgreSQL, Redis, MinIO instances — shared infrastructure
- Agent app's `settings.py` has connection strings for Alem-hosted infra — use as reference for Alem fallback config
- `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.example` — frontend expects API on port 8000
- `NEXT_PUBLIC_MAP_TILES_URL=http://localhost:8001` — frontend expects TiTiler on port 8001

</code_context>

<specifics>
## Specific Ideas

- The `structures` table should match Kazvodhoz spreadsheet columns so Phase 2 ingestion is a direct mapping without schema changes. The spreadsheet has 22 columns including: commissioning year, water source, carrying capacity (m³/s), total length (km) before/after reconstruction, earthwork vs lined length, suspended area (ha), KPD (efficiency) projected vs actual, serviced districts, rural district location, wear percentage, technical condition, cadastral number, state act.
- Dual SRID storage preserves original QazTRF-23 coordinates (important for cadastral accuracy in Kazakhstan) while also providing WGS84 for web display and OGC API compatibility.
- MinIO bucket names (`sujoly-structures`, `sujoly-imagery`, `sujoly-reports`) encode the architecture separation principle at the storage level — imagery evidence is never mixed with structure documents.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation-infrastructure*
*Context gathered: 2026-06-25*
