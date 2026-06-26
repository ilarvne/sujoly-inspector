# Phase 2: Data Ingestion & Spatial API - Context

**Gathered:** 2026-06-26
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the data layer that makes the catalog operational: ingesting the Kazvodhoz canal registry spreadsheet (444 records, 22 columns, Russian) into PostGIS, exposing structures via TiPG OGC API Features/Tiles for external GIS clients, providing REST CRUD endpoints for the frontend, and implementing multilingual full-text search (Russian, Kazakh, English) with pg_trgm fuzzy matching.

**In scope:** Spreadsheet ingestion pipeline (xlrd → PostGIS), TiPG container integration with OGC API Features/Tiles + CQL2 filtering, REST API for structures (list, retrieve, create, update, delete, search), multilingual FTS + pg_trgm search, Alembic migrations for schema additions (filterable columns, tsvector columns, trigram indexes).
**Out of scope:** Risk models and inspection intervals (Phase 3), discovery/matching algorithms (Phase 4), RAG agent integration (Phase 5), frontend UI (frontend workstream), OSM/satellite data ingestion (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### Coordinate Sourcing Strategy
- **D-01:** **CRITICAL FINDING: The Kazvodhoz spreadsheet (датасет.xls) contains NO coordinate data** — no lat/lon, no X/Y, no easting/northing columns in any of its 3 sheets. The success criterion "correctly transformed coordinates — no QazTRF-23 offset" cannot be satisfied from the spreadsheet alone. The QazTRF-23 / EPSG:10941 transformation requirement is moot for this data source.
- **D-02:** Make the `geometry` column nullable via Alembic migration (currently `NOT NULL` in the Phase 1 schema). Ingest all 444 records with their attribute data but NULL geometry. Coordinates will be assigned in Phase 4 (Discovery & Matching) when OSM tags, satellite water indices, and hydrography data are fused to locate structures. This keeps Phase 2 focused on attribute ingestion while not blocking on missing data.
- **D-03:** The researcher MUST investigate whether coordinates can be derived from the spreadsheet's location fields (district names, rural district names, water source names) via geocoding. The spreadsheet data is currently anonymized/placeholder ("Район 1" through "Район 440", "Сельский округ 1" through "440"), so geocoding may not be possible until real data is available. Flag this as a risk.

### TiPG Integration Approach
- **D-04:** Add TiPG as a standalone container in `docker-compose.yml` (matching Phase 1 decision D-03 which planned TiPG on port 8080 but was not implemented). TiPG connects to the same PostgreSQL instance via environment variables. This is the simplest approach and matches the original architecture plan.
- **D-05:** TiPG exposes the `structures` table as an OGC API Features collection with CQL2 filtering (INT-01). TiPG auto-generates TileJSON and StyleJSON endpoints for MapLibre consumption. The `structures` table's GiST spatial index (created in Phase 1 migration) supports efficient tile generation. TiPG's function-based collections can expose joined views (structures + structure_facts) if needed.
- **D-06:** TiPG configuration via environment variables: `TIPG_DATABASE_URL` pointing to PostgreSQL, `TIPG_HOST` and `TIPG_PORT` for the service. TiPG auto-discovers tables with geometry columns. No custom TiPG code needed — pure configuration.

### Schema Adaptation for Ingestion
- **D-07:** Keep the existing `StructureFactModel` (JSONB key-value) pattern from Phase 1. Map each of the 22 spreadsheet columns to a `structure_facts` row with `attribute_name` (column name) and `attribute_value` (JSONB with the value and unit). This respects the Phase 1 architecture and the provenance-per-fact design.
- **D-08:** Add filterable columns directly to the `structures` table via Alembic migration, needed for DATA-08 search/filter endpoints: `district` (String), `water_source` (String), `technical_condition` (String), `wear_percentage` (Float), `commissioning_year` (Integer), `cadastral_number` (String), `structure_count` (Integer). These are denormalized from the spreadsheet for query efficiency — the canonical data still lives in `structure_facts` with provenance, but these columns enable indexed filtering without JSONB traversal.
- **D-09:** The `name_ru` column gets the canal name/number from the spreadsheet (currently placeholder numbers like "1", "2"). `name_kk` and `name_en` remain NULL for now — translation is a separate concern. The `type` column gets "canal" (канал) for all records since the spreadsheet is specifically about canals.

### Multilingual Search Implementation
- **D-10:** Add generated tsvector columns to the `structures` table: `search_ts_ru`, `search_ts_kk`, `search_ts_en`. Use PostgreSQL's built-in FTS configurations (`simple` for Kazakh since no dedicated Kazakh config exists, `russian` for Russian, `english` for English). Create GIN indexes on each tsvector column. These index name columns + filterable text columns (district, water_source, technical_condition).
- **D-11:** Enable the `pg_trgm` extension and create trigram (GIN) indexes on `name_ru`, `name_kk`, `name_en` for fuzzy matching. This handles typos and partial name matches. Use `similarity()` function with a threshold (default 0.3) for fuzzy search.
- **D-12:** Search endpoint combines FTS ranking (`ts_rank_cd`) with trigram similarity (`similarity()`) in a single query. Results are ordered by a blended score. Search accepts a `lang` parameter (ru/kk/en) to select the appropriate tsvector column, with fallback to `simple` if no match. The `pg_trgm` fuzzy matching is language-agnostic and runs across all name columns regardless of lang parameter.

### REST API Design
- **D-13:** Follow the existing provenance route pattern (APIRouter prefix=/api/v1, Pydantic request/response models, service layer with async_session). New router at `/api/v1/structures` with standard CRUD: `GET /` (list with filters + pagination), `GET /{id}` (detail with structure_facts), `POST /` (create with provenance), `PUT /{id}` (update — creates new structure_facts with new provenance, expires old facts), `DELETE /{id}` (soft delete via status field or hard delete).
- **D-14:** Search endpoint at `GET /structures/search?q={query}&lang={ru|kk|en}&type={type}&district={district}&condition={condition}&bbox={minx,miny,maxx,maxy}&limit={n}`. Combines FTS + trigram + attribute filters + spatial bbox filter. Returns ranked results with match score.
- **D-15:** Ingestion endpoint at `POST /ingestion/kazvodhoz` — accepts optional file upload (defaults to the bundled `датасет.xls`), triggers a Celery task, returns a job ID immediately. Job status checkable via `GET /ingestion/kazvodhoz/{job_id}`. This is async because parsing 444 records with provenance creation is non-trivial.
- **D-16:** List endpoint `GET /structures` supports: `type`, `district`, `technical_condition`, `water_source` filters, `bbox` spatial filter, `offset`/`limit` pagination, and `q` text search. Response includes total count for pagination UI. GeoJSON response format option via `?format=geojson` for map clients.

### Ingestion Pipeline Design
- **D-17:** Celery task (`ingest_kazvodhoz`) triggered via API endpoint. Uses the sync database URL (psycopg) for bulk inserts — async SQLAlchemy is inefficient for bulk loading 444 records × 22 facts each. The task reads `датасет.xls` using `xlrd` (the only library that can read legacy .xls format; openpyxl does not support .xls).
- **D-18:** Read from the 'Корректировка' sheet (444 rows, matches requirement count exactly). The 'каналы' sheet has 451 rows with merged header rows and summary rows. The 'Лист1' sheet has 441 rows with additional columns (canal parameters, structure count). Cross-reference between sheets using the row number (Col 0) as the join key.
- **D-19:** Idempotent ingestion: check if a structure with the same `source_reference` (e.g., "kazvodhoz:каналы:row:N") already exists in provenance. If yes, skip or update (configurable via `--force` flag). This allows re-running ingestion after data corrections without creating duplicates.
- **D-20:** Provenance per ingestion run: one `ProvenanceModel` record per structure with `source_type="kazvodhoz_spreadsheet"`, `source_reference="датасет.xls:Корректировка:row:{N}"`, `confidence_level="HIGH"` (official registry data), `contributor="system:ingestion"`. Each `structure_fact` gets its own provenance pointing to the same source.

### the agent's Discretion
- TiPG Docker image tag and specific environment variable names (check TiPG 1.3.1 docs)
- Alembic migration numbering (continue from 0001)
- Pydantic schema field names and response structure details
- Celery task implementation details (chunking, progress reporting)
- Error handling and validation for malformed spreadsheet rows
- API response envelope format (plain data vs wrapped in {data, meta})
- Whether to add a `status` column for soft delete or use a separate mechanism
- Index strategy details (which columns get B-tree vs GIN vs GiST)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning & Requirements
- `.planning/workstreams/backend/ROADMAP.md` — Phase 2 goal, success criteria, requirements (DATA-01, DATA-08, INT-01, INT-03)
- `.planning/workstreams/backend/REQUIREMENTS.md` — Full requirement definitions with traceability
- `.planning/workstreams/backend/phases/01-foundation-infrastructure/01-CONTEXT.md` — Phase 1 decisions (infrastructure, schema, provenance model, patterns to follow)

### Technology Stack & Architecture
- `AGENTS.md` (STACK.md section) — Verified versions: TiPG 1.3.1, PostGIS 3.5.7, pgvector, FastAPI 0.128. Docker Compose service table with ports. TiPG vs Martin rationale.
- `.planning/PROJECT.md` — Architecture principle: "Every structure has one canonical asset record, many evidence sources, and a time-based condition history. PostGIS is the system of record."

### Existing Code Patterns to Follow
- `apps/api/src/api/routes/provenance.py` — Route pattern: APIRouter prefix=/api/v1, Pydantic Create/Response models, query params with filters, offset/limit pagination
- `apps/api/src/api/services/provenance_service.py` — Service pattern: async_session context, session.begin(), structlog, select with optional filters
- `apps/api/src/api/models/structure.py` — StructureModel + StructureFactModel ORM definitions (the schema Phase 2 builds on)
- `apps/api/src/api/models/provenance.py` — ProvenanceModel ORM (source_type, confidence_level, contributor, recorded_at)
- `apps/api/alembic/versions/0001_initial.py` — Migration pattern: op.create_table, Geometry columns, GiST indexes, CheckConstraint
- `apps/api/src/api/infrastructure/database.py` — Async engine, async_session factory, get_session dependency, Base declarative
- `apps/api/src/api/config/settings.py` — Settings pattern (API_ prefix, env loading)
- `apps/api/src/api/main.py` — App setup: lifespan, CORS, middleware, router registration
- `apps/api/pyproject.toml` — Dependencies already installed (fastapi, sqlalchemy, geoalchemy2, asyncpg, alembic, celery, pgvector, psycopg)

### Data Source
- `датасет.xls` — Kazvodhoz canal registry spreadsheet (3 sheets: 'каналы' 451 rows, 'Лист1' 441 rows, 'Корректировка' 444 rows). 22 columns in primary sheet. Russian language. NO coordinates. Anonymized/placeholder data. Last saved by Ilyas Kazambayev.

### Infrastructure
- `docker-compose.yml` — Current 5-service stack (postgres, redis, minio, api, celery-worker). TiPG needs to be added.
- `docker/postgres/init-extensions.sql` — PostGIS + pgvector extension creation. pg_trgm extension needs to be added here or via Alembic migration.
- `.env.example` — Environment variable template. TiPG config vars need to be added.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/api/src/api/routes/provenance.py` — Complete route pattern to mirror for structures CRUD: APIRouter, Pydantic models, query param filters, pagination
- `apps/api/src/api/services/provenance_service.py` — Service layer pattern: async_session, session.begin(), structlog, select with optional where clauses
- `apps/api/src/api/models/structure.py` — StructureModel (id, name_ru/kk/en, type, geometry, provenance_id) and StructureFactModel (structure_id, attribute_name, attribute_value JSONB, provenance_id, valid_from/to)
- `apps/api/src/api/infrastructure/database.py` — async_session factory and get_session dependency for route injection
- `apps/api/src/api/tasks/celery_tasks.py` — Celery app stubs ready for ingestion task implementation
- `apps/api/alembic/versions/0001_initial.py` — Migration pattern with Geometry, GiST indexes, CheckConstraint

### Established Patterns
- **Routes:** APIRouter with prefix="/api/v1", Pydantic Create/Response models with ConfigDict(from_attributes=True), HTTPException for 404
- **Services:** async with async_session() as session → async with session.begin() → add/flush/refresh for creates; select() with optional .where() for queries
- **Models:** SQLAlchemy 2.0 Mapped types, UUID primary keys, DateTime(timezone=True), GeoAlchemy2 Geometry
- **Migrations:** Alembic with op.create_table, op.create_index, op.execute for raw SQL (GiST indexes)
- **Config:** Pydantic Settings with env_prefix="API_", .env loading via python-dotenv
- **Docker:** Multi-service compose with health checks, depends_on with service_healthy condition
- **Testing:** pytest with pytest-asyncio, httpx for API tests, integration marker for Docker-dependent tests

### Integration Points
- `apps/api/src/api/main.py` — New structures router registered via `app.include_router()`
- `apps/api/src/api/tasks/celery_tasks.py` — Ingestion Celery task added here
- `docker-compose.yml` — TiPG service added alongside existing 5 services
- `docker/postgres/init-extensions.sql` — `CREATE EXTENSION pg_trgm` added
- `apps/api/alembic/versions/` — New migration (0002) for schema changes
- `.env.example` — TiPG environment variables added
- `датасет.xls` at repo root — Source data file for ingestion

</code_context>

<specifics>
## Specific Ideas

- The spreadsheet has 3 sheets with different column sets. 'Корректировка' (444 rows) matches the requirement count and has the cleanest structure (before/after reconstruction with notes). 'Лист1' (441 rows) has additional columns: canal parameters (width/depth as text), number of structures, year accepted. The ingestion should cross-reference between sheets using the row number as join key to get the richest possible dataset.
- The spreadsheet data is currently anonymized/placeholder: canal names are numbers ("1", "2"), districts are "Район 1" through "Район 440", water source is always "р. Иртыш" (Irtysh River — which is in East Kazakhstan, not Zhambyl Oblast). This suggests the real data will replace these placeholders. The ingestion pipeline must be robust to both placeholder and real data.
- The 'каналы' sheet has summary rows at the bottom (row 449: total length 833.33 km, row 450: grand total 2740.95 km) that must be excluded from ingestion.
- The 'Лист1' sheet has a grouping header "В республиканской собственности -(427)" indicating 427 structures are in republican ownership. This metadata could be captured as a structure_fact.
- The 'Корректировка' sheet has "Категория объектов" and "Группа объектов" groupings that may be useful for categorization.
- Canal parameters in 'Лист1' Col 16 are free-text Russian: "ширина по верху-3,2м, ширина по дну-1,0м, глубина-1,5м" (top width 3.2m, bottom width 1.0m, depth 1.5m). These could be parsed into structured facts.

</specifics>

<deferred>
## Deferred Ideas

- **Coordinate geocoding from district/water source names** — Could attempt to geocode structures from location field names, but data is currently placeholder. Belongs in Phase 4 (Discovery & Matching) where OSM/satellite data provides real coordinates.
- **Kazakh and English name translation** — name_kk and name_en columns exist but will be NULL after ingestion. Translation is a separate concern, possibly LLM-assisted in Phase 5.
- **Canal parameter text parsing** — Free-text Russian descriptions of canal dimensions (width, depth) could be parsed into structured facts. Nice-to-have but not required for Phase 2 success criteria.
- **Real-time ingestion monitoring dashboard** — Flower (Celery monitoring) is available but a custom ingestion progress dashboard is out of scope.
- **Spreadsheet validation and data quality reports** — Pre-ingestion validation (missing required fields, out-of-range values) could generate quality reports. Defer to a future data quality phase.

</deferred>

---

*Phase: 02-data-ingestion-spatial-api*
*Context gathered: 2026-06-26*
