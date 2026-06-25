# Phase 1: Foundation & Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-25
**Phase:** 01-foundation-infrastructure
**Areas discussed:** Infra deployment target, Project structure & deps, Provenance model design, DB schema scope

---

## Infra deployment target

| Option | Description | Selected |
|--------|-------------|----------|
| Local Docker Compose | Spin up local PostgreSQL/PostGIS, Redis, MinIO via docker-compose.yml. Full control, matches STACK.md, works offline. | |
| Use Alem hosted infra | Connect to existing Alem-hosted PostgreSQL/Redis/MinIO. No local containers, faster setup. Less control, can't run offline. | |
| Hybrid (local dev + Alem fallback) | Local Docker for development, configure to optionally use Alem infra via env vars. More flexible but more complex. | ✓ |

**User's choice:** Hybrid (local dev + Alem fallback)
**Notes:** The agent app already connects to Alem infra. The API should support both targets.

| Option | Description | Selected |
|--------|-------------|----------|
| Single compose file + .env switch | One docker-compose.yml, use .env to switch between local and Alem endpoints. | |
| Multi-file compose overlay | docker-compose.yml (base) + docker-compose.override.yml (local dev) + docker-compose.alem.yml (Alem). Docker Compose's -f overlay system. | ✓ |
| You decide | Pick whatever makes sense for a 2-3 person team. | |

**User's choice:** Multi-file compose overlay (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Include TiPG + TiTiler now | Include as containers in compose stack from Phase 1. Proves full architecture early. | ✓ |
| Defer TiPG/TiTiler to Phase 2 | Only PostgreSQL/PostGIS, Redis, MinIO, FastAPI, Celery in Phase 1. Leaner stack. | |
| You decide | Based on what makes sense for the walking skeleton. | |

**User's choice:** Include TiPG + TiTiler now (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| postgis/postgis:17-3.5 + manual pgvector | Use postgis/postgis:17-3.5 image and install pgvector via SQL. Matches STACK.md. | ✓ |
| Custom image with pgvector baked in | Extend postgis/postgis:17-3.5 with pgvector at build time. More reproducible. | |
| pgvector/pgvector:pg17 image | Pre-installed PostGIS + pgvector. Purpose-built. | |

**User's choice:** postgis/postgis:17-3.5 + manual pgvector (Recommended)

---

## Project structure & deps

| Option | Description | Selected |
|--------|-------------|----------|
| apps/api/ mirroring apps/agent/ | Own pyproject.toml, src/ layout, uv for deps. Consistent with existing codebase. | ✓ |
| Root pyproject.toml workspace | Single pyproject.toml at root with workspace deps. Shared deps, tighter coupling. | |
| You decide | Based on what works best for the team. | |

**User's choice:** apps/api/ mirroring apps/agent/ (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Mirror agent patterns | Pydantic Settings, structlog, OpenTelemetry, slowapi, multi-stage Dockerfile. Consistent. | ✓ |
| Fresh patterns | Standard logging, no OTel, simpler Dockerfile. Divergent style. | |
| Partial reuse | Config + logging + Docker only. Skip OTel and rate limiting for now. | |

**User's choice:** Mirror agent patterns (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| SQLAlchemy 2.0 + GeoAlchemy2 + Alembic | Type-safe PostGIS queries, async-native, industry standard. | ✓ |
| Raw asyncpg + manual SQL | Lighter, no ORM overhead, no type safety. | |
| SQLModel | Simpler models, less mature GeoAlchemy2 integration. | |

**User's choice:** SQLAlchemy 2.0 + GeoAlchemy2 + Alembic (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Celery + Redis broker | Battle-tested, Flower monitoring, Beat scheduling. | ✓ |
| FastAPI BackgroundTasks for now | Simpler, no extra service. Upgrade later. | |
| You decide | Based on what's right for the walking skeleton. | |

**User's choice:** Celery + Redis broker (Recommended)

---

## Provenance model design

| Option | Description | Selected |
|--------|-------------|----------|
| Separate provenance table + FK | Provenance table records each fact change. Entity has current_provenance_id FK. Clean, queryable, supports history. | ✓ |
| JSONB provenance column per record | Embedded source info. Simpler, no joins. Harder to query across records, no history. | |
| Append-only event log | Evidence_log table records every change. Full audit trail, CQRS-style, complex queries. | |
| Per-field JSONB + evidence_sources table | Per-field granularity via JSONB + separate sources table. Granular but complex. | |

**User's choice:** Separate provenance table + FK (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Polymorphic (entity_type + entity_id) | Single table for all provenance. One query for cross-entity. No FK enforcement. | ✓ |
| Per-entity provenance tables | FK enforcement, but more tables and duplicated schema. | |
| Single table with nullable FKs | FK enforcement + single table, but sparse columns. | |

**User's choice:** Polymorphic (entity_type + entity_id) (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| current_provenance_id FK + history | FK on entity pointing to latest. History in provenance table. Fast current reads. | ✓ |
| is_current boolean flag | No FK, boolean flag in provenance. Needs trigger to manage. | |
| Embedded JSONB current + history table | JSONB on entity for current + separate table for history. Best of both. | |

**User's choice:** current_provenance_id FK + history in provenance table (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Standard fields + valid_from/valid_to | source_type, source_reference, confidence, contributor, captured_at, valid_from, valid_to. | ✓ |
| Extended with raw_payload + verification | Same + raw_payload JSONB, transformation_notes, verification_status. Richer. | |
| Minimal fields only | source_type, source_reference, confidence, contributor, captured_at. Lean. | |

**User's choice:** Standard fields + valid_from/valid_to (Recommended)

---

## DB schema scope

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal: structures + provenance only | Just enough to prove provenance + architecture. Later phases add tables via Alembic. | ✓ |
| Core: structures + provenance + evidence_sources | Adds evidence_sources for INT-04 separation. | |
| Full foundation: all stub tables | Stubs for inspections, documents, risk_scores, candidates. Less migration churn. | |

**User's choice:** Minimal: structures + provenance only (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Core identity + geometry + status | id, trilingual names, type, geometry, provenance FK, status, condition_score, timestamps. | |
| Core + Kazvodhoz spreadsheet columns | Same + district, water_source, commissioning_year, technical_condition, wear_percentage. Direct Phase 2 mapping. | ✓ |
| Bare minimum | id, name, geometry, provenance FK, created_at. Add fields as needed. | |

**User's choice:** Core + Kazvodhoz spreadsheet columns

| Option | Description | Selected |
|--------|-------------|----------|
| Geography (WGS84) — transform at ingest | PostGIS Geography type, EPSG:4326. Transform QazTRF-23 at ingestion time. | |
| Geometry (SRID 4326) | Slightly faster for bounding box queries. Same storage, different semantics. | |
| Dual SRID (QazTRF-23 + WGS84) | Store both: original QazTRF-23 for accuracy + WGS84 for web display. Preserves original coordinates. | ✓ |

**User's choice:** Dual SRID (QazTRF-23 + WGS84)

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-create buckets + presigned URL endpoint | sujoly-structures, sujoly-imagery, sujoly-reports buckets. FastAPI presigned URL endpoint. | ✓ |
| Single bucket with path prefixes | One sujoly-data bucket with prefixes. Simpler, separation via conventions. | |
| Minimal proof-of-concept | One test bucket, upload test file, presigned URL. Full strategy in Phase 2. | |

**User's choice:** Pre-create buckets + presigned URL endpoint (Recommended)

---

## the agent's Discretion

- Docker Compose network configuration and volume naming conventions
- FastAPI app internal module structure (routers, models, schemas, services)
- Alembic migration directory structure and initial migration naming
- Celery task module organization (empty stubs for now)
- TiPG and TiTiler configuration file specifics
- Health check endpoint paths and response formats
- Docker Compose service naming conventions

## Deferred Ideas

None — discussion stayed within phase scope.
