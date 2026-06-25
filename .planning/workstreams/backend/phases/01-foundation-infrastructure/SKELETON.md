# Walking Skeleton — Zhambyl Hydraulic Structures Catalog (Backend)

**Phase:** 1
**Generated:** 2026-06-26

## Capability Proven End-to-End

A developer runs `docker compose up -d` and all five services (PostgreSQL/PostGIS/pgvector, Redis, MinIO, FastAPI, Celery) report healthy; the `/health/ready` endpoint verifies DB, Redis, and MinIO connectivity; the `/api/v1/provenance` endpoint creates and retrieves provenance records; and `/api/v1/minio/presign` generates working presigned URLs for MinIO object storage.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | FastAPI 0.138.1 + uvicorn 0.49.0 | Async, auto OpenAPI docs, type-hint validation, lifespan context managers. Matches existing agent app ecosystem. |
| Data layer | PostgreSQL 17 + PostGIS 3.5.7 + pgvector + pg_trgm | PostGIS is system of record for vector features. pgvector for hybrid search (Phase 5). pg_trgm for fuzzy matching (Phase 2). Custom Dockerfile extends postgis/postgis:17-3.5 with pgvector from PGDG apt. |
| Object storage | MinIO (S3-compatible) | Binary assets (COGs, documents, photos) never touch PostGIS. Three buckets: sujoly-imagery, sujoly-documents, sujoly-photos. Presigned URLs with short expiry. |
| Cache / broker | Redis 7-alpine | Celery message broker, API response cache. Single Redis instance serves both. |
| Background tasks | Celery 5.6.3 + Redis broker | Durable, retryable, monitorable. FastAPI BackgroundTasks are in-process only. Shared Docker image with FastAPI app. |
| Auth | None (Phase 1) | No authentication in foundation phase. RBAC (admin/engineer/inspector/viewer) arrives in Phase 3 (RISK-07). |
| Deployment target | Docker Compose (local dev) | Single-host, 2-3 person team. Remote alem.ai infrastructure exists for production/demo, not local dev. Local .env uses Docker service credentials. |
| Directory layout | `apps/api/src/api/` with feature-folders | Matches existing `apps/agent/src/agent/` convention. Subdirs: config, infrastructure, models, routes, services, tasks, utils. |
| Package manager | uv (not pip) | Matches existing agent app convention. Lockfile reproducibility. |
| Schema management | Alembic migrations (not create_all) | Version-controlled, reversible. GeoAlchemy2 alembic_helpers for spatial types. Agent app uses create_all — new API must not follow that anti-pattern. |
| Logging | structlog 26.1.0 | JSON in production, console in dev. Follows existing agent app pattern. |
| Config | Pydantic Settings (env_prefix="API_") | Type-validated env vars. Local Docker defaults, NOT remote alem.ai credentials (deviation from agent app). |
| ORM style | SQLAlchemy 2.0 Mapped + mapped_column | Modern type-hint style. Agent app uses legacy Column() — new API uses 2.0 style. |

## Stack Touched in Phase 1

- [x] Project scaffold (FastAPI app, uv, pyproject.toml, Dockerfile, ruff, pytest)
- [x] Routing — `/health/live`, `/health/ready`, `/api/v1/provenance`, `/api/v1/minio/presign`
- [x] Database — provenance table (create + retrieve + query), structures + structure_facts tables with PostGIS Geometry
- [x] Object storage — MinIO presigned URLs for upload and download (architecture separation proof)
- [x] Deployment — `docker compose up -d` exercises full 5-service stack

## Out of Scope (Deferred to Later Slices)

- Authentication / RBAC (Phase 3, RISK-07)
- Kazvodhoz data ingestion (Phase 2, DATA-01)
- OGC API Features/Tiles via TiPG (Phase 2, INT-01)
- Risk models and inspection intervals (Phase 3)
- Discovery and matching (Phase 4)
- RAG agent integration (Phase 5)
- Frontend UI (frontend workstream)
- TiTiler raster serving (Phase 4, INT-02)
- STAC catalog (Phase 4, INT-02)
- pgvector hybrid search (Phase 5, AI-03)
- OCR pipeline (Phase 4, DATA-03)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: Kazvodhoz registry ingested into PostGIS, searchable via OGC API (TiPG) and REST with multilingual FTS
- Phase 3: Risk-informed inspection intervals, repair statuses, inspection history, document attachments, RBAC, exports
- Phase 4: Evidence-fusion candidate discovery, four-state matching, STAC catalog, OCR pipeline
- Phase 5: RAG agent connected to platform with hybrid search and copilot tool endpoints
