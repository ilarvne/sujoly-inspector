# Phase 2: Data Ingestion & Spatial API - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-26
**Phase:** 02-data-ingestion-spatial-api
**Mode:** --auto (autonomous selection)
**Areas discussed:** Coordinate sourcing, TiPG integration, Schema adaptation, Multilingual search, REST API design, Ingestion pipeline

---

## Coordinate Sourcing Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Make geometry nullable, defer coordinates to Phase 4 | Spreadsheet has NO coordinates. Ingest attributes now, assign coordinates during discovery matching. | ✓ |
| Geocode from district/water source names | Attempt to derive coordinates from location text fields. | |
| Require coordinates before ingestion | Block ingestion until coordinate data is provided. | |

**[auto] Selected:** "Make geometry nullable, defer coordinates to Phase 4" (recommended default)
**Notes:** CRITICAL finding — the spreadsheet (датасет.xls) has no coordinate columns in any of its 3 sheets. Data is anonymized/placeholder ("Район 1" through "Район 440"). The QazTRF-23 transformation requirement is moot. Researcher must investigate coordinate sourcing options.

---

## TiPG Integration Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone TiPG container in docker-compose | Add TiPG as a separate service connecting to PostgreSQL. Matches D-03 plan. | ✓ |
| Embed TiPG factory in FastAPI app | Mount TiPG's FastAPI router inside the main API app. | |
| Use Martin instead | Switch to Martin vector tile server (but no OGC API Features support). | |

**[auto] Selected:** "Standalone TiPG container in docker-compose" (recommended default)
**Notes:** TiPG was planned in Phase 1 (D-03, port 8080) but not implemented. Adding as standalone container is simplest and matches architecture. TiPG auto-discovers tables with geometry columns and provides OGC API Features + Tiles + CQL2 filtering.

---

## Schema Adaptation for Ingestion

| Option | Description | Selected |
|--------|-------------|----------|
| Keep StructureFactModel, add filterable columns to structures | Map spreadsheet columns to structure_facts rows, add denormalized filter columns for query efficiency. | ✓ |
| Flatten all columns onto structures table | Add all 22 spreadsheet columns directly to structures table. | |
| Use only StructureFactModel, no denormalization | Store everything as JSONB facts, query via JSONB operators. | |

**[auto] Selected:** "Keep StructureFactModel, add filterable columns to structures" (recommended default)
**Notes:** Respects Phase 1 architecture (provenance-per-fact) while enabling efficient filtered queries. Denormalized columns: district, water_source, technical_condition, wear_percentage, commissioning_year, cadastral_number, structure_count.

---

## Multilingual Search Implementation

| Option | Description | Selected |
|--------|-------------|----------|
| Generated tsvector columns + pg_trgm indexes | Per-language tsvector columns with GIN indexes, trigram indexes on name columns, blended ranking. | ✓ |
| Separate search table | Materialized view or separate search table updated on writes. | |
| External search engine (Meilisearch/Elasticsearch) | Add a dedicated search service. | |

**[auto] Selected:** "Generated tsvector columns + pg_trgm indexes" (recommended default)
**Notes:** PostgreSQL-native, no new infrastructure. Uses `russian` config for RU, `simple` for KK (no dedicated Kazakh FTS config), `english` for EN. pg_trgm for fuzzy matching across all name columns. Blended score: ts_rank_cd + similarity().

---

## REST API Design

| Option | Description | Selected |
|--------|-------------|----------|
| Follow provenance route pattern with /api/v1/structures | Mirror existing route/service/model pattern. CRUD + search + ingestion endpoints. | ✓ |
| GraphQL API | Single endpoint with typed queries. | |
| OGC API Features only (no custom REST) | Rely on TiPG for all data access. | |

**[auto] Selected:** "Follow provenance route pattern with /api/v1/structures" (recommended default)
**Notes:** Consistent with Phase 1 code. Endpoints: GET / (list+filter), GET /{id}, POST /, PUT /{id}, DELETE /{id}, GET /search, POST /ingestion/kazvodhoz. GeoJSON format option for map clients.

---

## Ingestion Pipeline Design

| Option | Description | Selected |
|--------|-------------|----------|
| Celery task via API endpoint, idempotent | Async Celery task reading .xls with xlrd, idempotent re-import, sync DB for bulk inserts. | ✓ |
| Synchronous CLI command | Management script run once, no API endpoint. | |
| Direct API endpoint (synchronous) | Parse and insert in the request handler. | |

**[auto] Selected:** "Celery task via API endpoint, idempotent" (recommended default)
**Notes:** Uses xlrd (only library supporting legacy .xls). Reads 'Корректировка' sheet (444 rows). Sync database URL (psycopg) for bulk inserts. Idempotent via source_reference check. One provenance per structure, facts reference same provenance.

---

## the agent's Discretion

- TiPG Docker image tag and environment variable names
- Alembic migration numbering
- Pydantic schema field names and response structure
- Celery task chunking and progress reporting
- Error handling for malformed spreadsheet rows
- API response envelope format
- Soft delete vs hard delete mechanism
- Index strategy details

## Deferred Ideas

- Coordinate geocoding from district/water source names (Phase 4)
- Kazakh and English name translation (Phase 5, LLM-assisted)
- Canal parameter text parsing into structured facts (future enhancement)
- Real-time ingestion monitoring dashboard (Flower available, custom dashboard out of scope)
- Spreadsheet validation and data quality reports (future data quality phase)
