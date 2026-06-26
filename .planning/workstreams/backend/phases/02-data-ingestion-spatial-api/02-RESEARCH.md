# Phase 2: Data Ingestion & Spatial API - Research

**Researched:** 2026-06-26
**Domain:** Data ingestion (xlrd → PostGIS), OGC API Features/Tiles (TiPG), REST CRUD + multilingual FTS + pg_trgm fuzzy search
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** CRITICAL FINDING: The Kazvodhoz spreadsheet (датасет.xls) contains NO coordinate data — no lat/lon, no X/Y columns in any of its 3 sheets. The QazTRF-23 transformation requirement is moot for this data source.
- **D-02:** Make the `geometry` column nullable via Alembic migration (currently `NOT NULL` in Phase 1 schema). Ingest all 444 records with NULL geometry. Coordinates assigned in Phase 4.
- **D-03:** Researcher MUST investigate coordinate derivation from location fields. Data is currently anonymized/placeholder ("Район 1" through "Район 440"). Flag as risk.
- **D-04:** Add TiPG as standalone container in docker-compose.yml. TiPG connects to same PostgreSQL via env vars.
- **D-05:** TiPG exposes `structures` table as OGC API Features collection with CQL2 filtering. TiPG auto-generates TileJSON and StyleJSON endpoints for MapLibre.
- **D-06:** TiPG configuration via environment variables: `DATABASE_URL` pointing to PostgreSQL, host/port for service. TiPG auto-discovers tables with geometry columns.
- **D-07:** Keep existing `StructureFactModel` (JSONB key-value) pattern. Map each of 22 spreadsheet columns to a `structure_facts` row.
- **D-08:** Add filterable columns directly to `structures` table: `district`, `water_source`, `technical_condition`, `wear_percentage`, `commissioning_year`, `cadastral_number`, `structure_count`.
- **D-09:** `name_ru` gets canal name/number from spreadsheet. `name_kk` and `name_en` remain NULL. `type` gets "canal" for all records.
- **D-10:** Add generated tsvector columns: `search_ts_ru`, `search_ts_kk`, `search_ts_en`. Use `simple` for Kazakh, `russian` for Russian, `english` for English. GIN indexes on each.
- **D-11:** Enable `pg_trgm` extension, create trigram (GIN) indexes on `name_ru`, `name_kk`, `name_en` for fuzzy matching. Use `similarity()` with threshold 0.3.
- **D-12:** Search endpoint combines FTS ranking (`ts_rank_cd`) with trigram similarity (`similarity()`) in a single query. Accepts `lang` parameter (ru/kk/en).
- **D-13:** Follow existing provenance route pattern. New router at `/api/v1/structures` with standard CRUD.
- **D-14:** Search endpoint at `GET /structures/search?q={query}&lang={ru|kk|en}&type={type}&district={district}&condition={condition}&bbox={minx,miny,maxx,maxy}&limit={n}`.
- **D-15:** Ingestion endpoint at `POST /ingestion/kazvodhoz` — accepts optional file upload, triggers Celery task, returns job ID. Status via `GET /ingestion/kazvodhoz/{job_id}`.
- **D-16:** List endpoint supports: `type`, `district`, `technical_condition`, `water_source` filters, `bbox` spatial filter, `offset`/`limit` pagination, `q` text search. GeoJSON format option via `?format=geojson`.
- **D-17:** Celery task using sync database URL (psycopg) for bulk inserts. Uses `xlrd` to read .xls.
- **D-18:** Read from 'Корректировка' sheet (444 rows). Cross-reference between sheets using row number as join key.
- **D-19:** Idempotent ingestion: check if structure with same `source_reference` already exists. Skip or update via `--force` flag.
- **D-20:** Provenance per ingestion run: one `ProvenanceModel` per structure with `source_type="kazvodhoz_spreadsheet"`, `source_reference="датасет.xls:Корректировка:row:{N}"`, `confidence_level="HIGH"`, `contributor="system:ingestion"`.

### the agent's Discretion
- TiPG Docker image tag and specific environment variable names (check TiPG 1.3.1 docs)
- Alembic migration numbering (continue from 0001)
- Pydantic schema field names and response structure details
- Celery task implementation details (chunking, progress reporting)
- Error handling and validation for malformed spreadsheet rows
- API response envelope format (plain data vs wrapped in {data, meta})
- Whether to add a `status` column for soft delete or use a separate mechanism
- Index strategy details (which columns get B-tree vs GIN vs GiST)

### Deferred Ideas (OUT OF SCOPE)
- Coordinate geocoding from district/water source names (Phase 4)
- Kazakh and English name translation (separate concern, possibly LLM-assisted in Phase 5)
- Canal parameter text parsing (nice-to-have, not required for Phase 2)
- Real-time ingestion monitoring dashboard (Flower available but custom dashboard out of scope)
- Spreadsheet validation and data quality reports (future data quality phase)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | System can ingest the Kazvodhoz canal registry spreadsheet (444 records, 22 columns, Russian) into PostGIS with coordinate transformation (QazTRF-23 / EPSG:10941) | Spreadsheet analysis (xlrd), Celery ingestion pipeline, nullable geometry for missing coordinates. QazTRF-23 is moot — no coordinate data in spreadsheet (D-01). Coordinates deferred to Phase 4. |
| DATA-08 | System provides search and filter endpoints by name, type, condition, district, or location using multilingual full-text search (Russian, Kazakh, English) and fuzzy matching (pg_trgm) | Generated tsvector columns (D-10), pg_trgm trigram indexes (D-11), combined FTS + trigram search query (D-12), filterable denormalized columns (D-08) |
| INT-01 | System exposes OGC API Features (Part 1 Core, Part 3 Filtering/CQL2) and OGC API Tiles (Part 1 Core) via TiPG for external GIS clients | TiPG Docker container configuration, auto-discovery of `structures` table, CQL2 filtering, TileJSON/StyleJSON endpoints for MapLibre |
| INT-03 | System exposes a REST API for the application frontend (CRUD, search, copilot, ingestion, sync endpoints) | FastAPI route patterns following provenance model, CRUD endpoints, search endpoint, ingestion endpoint with Celery task |
</phase_requirements>

## Summary

Phase 2 delivers the data layer that makes the catalog operational: ingesting 444 Kazvodhoz canal records from a legacy `.xls` spreadsheet into PostGIS, exposing them via TiPG OGC API Features/Tiles for external GIS clients, providing REST CRUD endpoints for the frontend, and implementing multilingual full-text search with pg_trgm fuzzy matching.

The most critical finding is that the spreadsheet contains NO coordinate data (D-01). All records will be ingested with NULL geometry, with coordinates deferred to Phase 4's discovery/matching pipeline. PostGIS 3.5.7 correctly handles NULL geometries — `ST_AsGeoJSON` produces valid `"geometry": null` output (fixed in 3.5.0, ticket #5597). TiPG discovers tables with geometry columns regardless of NULL values and serves features with null geometry correctly via the Features API. Tiles will simply skip NULL-geometry rows.

The spreadsheet has 3 sheets with different column counts: 'Корректировка' (13 cols, 434 data rows), 'Лист1' (19 cols, additional canal parameters/structure count/year), and 'каналы' (22 cols, 444 data rows, has district/wear%/condition/cadastral fields). The ingestion must cross-reference sheets using the № column as join key to assemble the richest dataset. The 'Корректировка' sheet alone does NOT contain the filterable columns needed for D-08 (district, wear_percentage, technical_condition, cadastral_number) — these are in 'каналы' and 'Лист1'.

**Primary recommendation:** Build a 3-wave plan: (1) Schema migration + TiPG container, (2) Celery ingestion pipeline with cross-sheet data assembly, (3) REST CRUD + search endpoints. Use generated tsvector columns with `setweight()` for ranked multilingual FTS, GIN trigram indexes for fuzzy matching, and `psycopg` sync connections for bulk loading via SQLAlchemy 2.0 `session.execute(insert(Model), values)`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Spreadsheet ingestion (xlrd parsing) | API / Backend (Celery worker) | — | Celery task reads .xls, transforms rows to ORM models, bulk-inserts via sync psycopg |
| OGC API Features/Tiles serving | CDN / Static (TiPG container) | Database / Storage (PostGIS) | TiPG is a standalone FastAPI app that reads directly from PostGIS — no custom code needed |
| REST CRUD endpoints | API / Backend (FastAPI) | Database / Storage (PostGIS) | FastAPI routes follow provenance pattern, service layer with async SQLAlchemy |
| Multilingual FTS + fuzzy search | Database / Storage (PostgreSQL) | API / Backend (FastAPI) | Generated tsvector columns + pg_trgm indexes are database-level; FastAPI constructs queries |
| Spatial bbox filtering | Database / Storage (PostGIS) | API / Backend (FastAPI) | `ST_MakeEnvelope` + `ST_Intersects` in SQL, exposed via FastAPI query params |
| Schema migration (nullable geometry, new columns, indexes) | Database / Storage (PostgreSQL) | — | Alembic migration 0002 handles all DDL |
| Coordinate assignment | — (deferred to Phase 4) | — | No coordinates in source data; geometry is NULL until Phase 4 discovery |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.128.x | REST API framework | Already installed in Phase 1. Provides route patterns, Pydantic validation, OpenAPI docs. [VERIFIED: pyproject.toml] |
| SQLAlchemy | 2.0+ | Async ORM + sync bulk insert | Already installed. Async for API routes, sync for Celery bulk loading. [VERIFIED: pyproject.toml] |
| GeoAlchemy2 | 0.18+ | PostGIS spatial types | Already installed. `Geometry("Point", srid=4326)` type, `func.ST_*` spatial functions. [VERIFIED: pyproject.toml] |
| Alembic | 1.13+ | Database migrations | Already installed. Migration 0002 adds columns, indexes, generated columns. [VERIFIED: pyproject.toml] |
| Celery | 5.4+ | Background task queue | Already installed. Ingestion task runs in celery-worker container. [VERIFIED: pyproject.toml] |
| psycopg | 3.2+ (binary, pool) | Sync PostgreSQL driver | Already installed. Used for bulk inserts in Celery task via `sync_database_url`. [VERIFIED: pyproject.toml] |
| asyncpg | 0.29+ | Async PostgreSQL driver | Already installed. Used by FastAPI routes via `database_url`. [VERIFIED: pyproject.toml] |
| Pydantic Settings | 2.x | Config management | Already installed. Settings pattern with `API_` env prefix. [VERIFIED: pyproject.toml] |
| TiPG | 1.3.1 | OGC API Features + Tiles | **NEW container.** Docker image `ghcr.io/developmentseed/tipg:latest`. Auto-discovers PostGIS tables. No custom code — pure configuration. [CITED: developmentseed.org/tipg] |
| xlrd | 2.0.2 | Read legacy .xls files | **NEW dependency.** Only library that reads .xls format (openpyxl does not). BSD licensed, stable since 2020. [VERIFIED: PyPI + slopcheck OK] |
| PostgreSQL | 17.x | Primary database | Already running. PostGIS 3.5.7 + pgvector + pg_trgm extensions. [VERIFIED: docker-compose.yml] |
| PostGIS | 3.5.7 | Spatial extension | Already installed. 3.5.7 fixes NULL geometry GeoJSON output (ticket #5597, fixed in 3.5.0). [CITED: postgis.net] |
| pg_trgm | (built-in PG ext) | Trigram fuzzy matching | Already enabled in `init-extensions.sql`. Provides `similarity()`, `%` operator, `gin_trgm_ops`. [VERIFIED: docker/postgres/init-extensions.sql] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| structlog | 24.1+ | Structured logging | Already installed. Use in service layer and Celery task. [VERIFIED: pyproject.toml] |
| python-multipart | 0.0.9+ | File upload parsing | Already installed. For ingestion endpoint file upload. [VERIFIED: pyproject.toml] |
| Redis | 7.x | Celery broker + result backend | Already running. Celery task results stored here for job status polling. [VERIFIED: docker-compose.yml] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TiPG | Martin | Martin has no OGC API Features support (tile-only). TiPG provides both Features + Tiles. [CITED: AGENTS.md STACK.md] |
| TiPG | pg_featureserv | CrunchyData's server. Only does Features, not Tiles. Less actively maintained. [CITED: AGENTS.md STACK.md] |
| xlrd | pandas.read_excel | pandas wraps xlrd for .xls files but adds heavy dependency. Direct xlrd is lighter. [ASSUMED] |
| Generated tsvector columns | Trigger-based tsvector | Generated columns are simpler (PG 12+), no trigger maintenance. Triggers needed only for complex logic. [CITED: postgresql.org/docs] |
| psycopg sync bulk insert | asyncpg bulk insert | Async is inefficient for bulk loading 444×22 rows. Sync psycopg with SQLAlchemy 2.0 batch insert is standard. [CITED: sqlalchemy.org docs] |

**Installation:**
```bash
# Only xlrd is new — add to pyproject.toml dependencies
# All other packages already installed in Phase 1
pip install xlrd  # Version 2.0.2 (latest, stable since 2020)
```

**Version verification:**
```
xlrd: 2.0.2 (latest, PyPI, slopcheck OK)
TiPG: 1.3.1 (PyPI, Feb 2026) — Docker image ghcr.io/developmentseed/tipg:latest
PostGIS: 3.5.7 (June 2026) — includes NULL geometry GeoJSON fix
pg_trgm: built-in PostgreSQL extension — already enabled in init-extensions.sql
All other packages: already in pyproject.toml from Phase 1
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| xlrd | PyPI | ~15 years (since 2010) | High (widely used) | github.com/python-excel/xlrd | [OK] | Approved |
| TiPG | GHCR (Docker) | ~3 years (since 2023) | N/A (container) | github.com/developmentseed/tipg | N/A | Approved (official Development Seed image) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*All other packages (fastapi, sqlalchemy, geoalchemy2, alembic, celery, psycopg, asyncpg, pydantic-settings, structlog, python-multipart) were already installed in Phase 1 and verified at that time.*

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    Docker Network                        │
                    │                                                         │
  POST /ingestion   │  ┌──────────┐    ┌─────────┐    ┌──────────────────┐   │
  ─────────────────►│  │  FastAPI  │    │  Redis  │    │  Celery Worker    │   │
  GET /structures   │  │  (port    │    │ (broker)│    │  (ingestion task) │   │
  GET /structures/  │  │   8000)   │    │         │    │                   │   │
  search            │  │           │    │         │    │  xlrd → ORM →     │   │
                    │  │  Routes:  │    │         │    │  psycopg bulk     │   │
  QGIS / ArcGIS     │  │  /api/v1/ │    │         │    │  insert           │   │
  ─────────────────►│  │  structures│   │         │    │                   │   │
  OGC API Features  │  │  /api/v1/ │    │         │    │  ┌──────────┐     │   │
  OGC API Tiles     │  │  ingestion│    │         │    │  │ датасет  │     │   │
                    │  │  /api/v1/ │    │         │    │  │  .xls    │     │   │
                    │  │  provenance│   │         │    │  └──────────┘     │   │
                    │  └─────┬─────┘    └─────────┘    └────────┬──────────┘   │
                    │        │             ▲                     │              │
                    │        │ async       │ broker              │ sync         │
                    │        │ (asyncpg)   │                     │ (psycopg)    │
                    │        ▼             │                     ▼              │
                    │  ┌──────────────────────────────────────────────────┐    │
                    │  │         PostgreSQL 17 + PostGIS 3.5.7             │    │
                    │  │         + pgvector + pg_trgm                      │    │
                    │  │                                                   │    │
                    │  │  structures: id, name_ru/kk/en, type,             │    │
                    │  │    geometry (NULLABLE), provenance_id,             │    │
                    │  │    district, water_source, technical_condition,    │    │
                    │  │    wear_percentage, commissioning_year,           │    │
                    │  │    cadastral_number, structure_count,             │    │
                    │  │    search_ts_ru/kk/en (GENERATED tsvector)         │    │
                    │  │                                                   │    │
                    │  │  structure_facts: JSONB key-value + provenance     │    │
                    │  │  provenance: source_type, confidence, reference    │    │
                    │  └──────────────────────┬────────────────────────────┘    │
                    │                         │                               │
                    │           ┌─────────────┴──────────────┐                │
                    │           │     TiPG Container          │                │
                    │           │     (port 8080)             │                │
                    │           │                             │                │
                    │           │  /collections               │                │
                    │           │  /collections/public.       │                │
                    │           │   structures/items          │                │
                    │           │  /collections/public.       │                │
                    │           │   structures/tiles/...      │                │
                    │           │  + CQL2 filtering           │                │
                    │           │  + TileJSON + StyleJSON     │                │
                    │           └─────────────────────────────┘                │
                    └─────────────────────────────────────────────────────────┘
```

Data flow:
1. **Ingestion:** POST /ingestion/kazvodhoz → FastAPI → Celery task queued via Redis → Worker reads .xls with xlrd → bulk insert via psycopg sync → structures + structure_facts + provenance rows created
2. **REST API:** GET /structures → FastAPI async route → asyncpg → PostgreSQL (with FTS + trigram + bbox filters) → JSON response
3. **OGC API:** QGIS → TiPG container → direct PostGIS query (ST_AsMVT for tiles, GeoJSON for features) → CQL2 filtering supported

### Recommended Project Structure
```
apps/api/src/api/
├── routes/
│   ├── provenance.py        # Existing (Phase 1)
│   ├── structures.py        # NEW — CRUD + list + search endpoints
│   └── ingestion.py         # NEW — POST /ingestion/kazvodhoz + GET status
├── services/
│   ├── provenance_service.py # Existing (Phase 1)
│   ├── structure_service.py  # NEW — async CRUD + search queries
│   └── ingestion_service.py  # NEW — xlrd parsing + bulk insert logic
├── models/
│   ├── structure.py          # MODIFIED — add filterable columns, tsvector columns
│   └── provenance.py         # Existing (Phase 1)
├── schemas/
│   └── structures.py         # NEW — Pydantic request/response models
├── tasks/
│   └── celery_tasks.py       # MODIFIED — add ingest_kazvodhoz task
├── infrastructure/
│   └── database.py           # Existing (Phase 1) — add sync engine for Celery
└── config/
    └── settings.py           # MODIFIED — add TiPG-related settings if needed

apps/api/alembic/versions/
└── 0002_add_filterable_columns_and_search.py  # NEW migration

apps/api/tests/
├── test_structures.py        # NEW — CRUD + search endpoint tests
├── test_ingestion.py         # NEW — ingestion task tests
└── conftest.py               # MODIFIED — add structure fixtures
```

### Pattern 1: Generated tsvector Column with Weighted Multilingual FTS
**What:** PostgreSQL generated columns that auto-compute tsvector from text columns, with GIN indexes for fast search.
**When to use:** Any table with searchable text columns in multiple languages.
**Example:**
```sql
-- Source: PostgreSQL official docs (postgresql.org/docs/current/textsearch-tables.html)
-- + runebook.dev Russian FTS guide + multiple GitHub examples verified via grep_app

-- Russian FTS (with stemming and stop words)
ALTER TABLE structures ADD COLUMN search_ts_ru tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('russian', coalesce(name_ru, '')), 'A') ||
        setweight(to_tsvector('russian', coalesce(district, '')), 'B') ||
        setweight(to_tsvector('russian', coalesce(water_source, '')), 'B') ||
        setweight(to_tsvector('russian', coalesce(technical_condition, '')), 'C')
    ) STORED;

-- Kazakh FTS (no dedicated config — 'simple' does lowercasing + tokenization only)
ALTER TABLE structures ADD COLUMN search_ts_kk tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(name_kk, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(district, '')), 'B')
    ) STORED;

-- English FTS
ALTER TABLE structures ADD COLUMN search_ts_en tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name_en, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(district, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(water_source, '')), 'B')
    ) STORED;

-- GIN indexes for fast full-text search
CREATE INDEX ix_structures_search_ts_ru ON structures USING GIN (search_ts_ru);
CREATE INDEX ix_structures_search_ts_kk ON structures USING GIN (search_ts_kk);
CREATE INDEX ix_structures_search_ts_en ON structures USING GIN (search_ts_en);
```

Query pattern (from PostgreSQL docs):
```sql
-- Search using the generated column + GIN index
SELECT *, ts_rank_cd(search_ts_ru, query) AS rank
FROM structures, plainto_tsquery('russian', 'канал Иртыш') query
WHERE search_ts_ru @@ query
ORDER BY rank DESC
LIMIT 20;
```

### Pattern 2: pg_trgm Fuzzy Matching with GIN Index
**What:** Trigram-based similarity search for typo-tolerant name matching.
**When to use:** When users may misspell or partially type structure names.
**Example:**
```sql
-- Source: PostgreSQL official docs (postgresql.org/docs/current/pgtrgm.html)
-- pg_trgm already enabled in init-extensions.sql

-- GIN trigram indexes on name columns
CREATE INDEX ix_structures_name_ru_trgm ON structures USING GIN (name_ru gin_trgm_ops);
CREATE INDEX ix_structures_name_kk_trgm ON structures USING GIN (name_kk gin_trgm_ops);
CREATE INDEX ix_structures_name_en_trgm ON structures USING GIN (name_en gin_trgm_ops);

-- Fuzzy search query: filter with % operator, rank with similarity()
SELECT *, similarity(name_ru, 'канал 42') AS trgm_score
FROM structures
WHERE name_ru % 'канал 42'
ORDER BY trgm_score DESC
LIMIT 10;

-- Combined FTS + trigram search (D-12)
SELECT *,
    ts_rank_cd(search_ts_ru, plainto_tsquery('russian', $1)) AS fts_rank,
    GREATEST(
        similarity(name_ru, $1),
        similarity(name_kk, $1),
        similarity(name_en, $1)
    ) AS trgm_score,
    (ts_rank_cd(search_ts_ru, plainto_tsquery('russian', $1)) * 0.7 +
     GREATEST(similarity(name_ru, $1), similarity(name_kk, $1), similarity(name_en, $1)) * 0.3
    ) AS blended_score
FROM structures
WHERE search_ts_ru @@ plainto_tsquery('russian', $1)
   OR name_ru % $1 OR name_kk % $1 OR name_en % $1
ORDER BY blended_score DESC
LIMIT 20;
```

**Important note on index choice:** GIN indexes are optimal for filter-only queries (`WHERE col % 'query'`). GiST indexes are needed for KNN-style ordering (`ORDER BY col <-> 'query'`). Since our query pattern filters with `%` and sorts with `similarity()` function (not the `<->` operator), GIN is the correct choice. [CITED: postgresql.org/docs/current/pgtrgm.html + jamongx.com pg_trgm guide]

### Pattern 3: TiPG Container Configuration
**What:** Standalone TiPG container that auto-discovers PostGIS tables and serves OGC API Features + Tiles.
**When to use:** When external GIS clients need OGC API Features/Tiles access to PostGIS data.
**Example:**
```yaml
# docker-compose.yml addition
# Source: TiPG official docs (developmentseed.org/tipg) + GitHub docker-compose.yml

tipg:
  image: ghcr.io/developmentseed/tipg:latest
  command: >
    gunicorn -k uvicorn.workers.UvicornWorker tipg.main:app
    --bind 0.0.0.0:8080 --workers 2
  environment:
    DATABASE_URL: postgresql://${POSTGRES_USER:-sujoly}:${POSTGRES_PASSWORD:-sujoly_dev}@postgres:5432/${POSTGRES_DB:-sujoly}
    TIPG_CORS_ORIGIN: "*"
    TIPG_DEFAULT_FEATURES_LIMIT: "1000"
    TIPG_MAX_FEATURES_PER_QUERY: "10000"
    TIPG_CATALOG_TTL: "300"
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

Key TiPG behavior:
- **Auto-discovery:** Scans `public` schema for tables with geometry/geography columns. `structures` table will be discovered as collection `public.structures`. [CITED: developmentseed.org/tipg/user_guide/configuration]
- **Features endpoint:** `/collections/public.structures/items` — GeoJSON response with CQL2 filtering (`filter` param), bbox, limit/offset, property filters. [CITED: developmentseed.org/tipg/user_guide/endpoints]
- **Tiles endpoint:** `/collections/public.structures/tiles/WebMercatorQuad/{z}/{x}/{y}` — MVT tiles via `ST_AsMVT`. [CITED: developmentseed.org/tipg/user_guide/endpoints]
- **MapLibre integration:** `/collections/public.structures/tiles/WebMercatorQuad/tilejson.json` and `style.json` endpoints ready for MapLibre consumption. [CITED: developmentseed.org/tipg/user_guide/endpoints]
- **CQL2 filtering:** `?filter=type='canal' AND district LIKE 'Район%'&filter-lang=cql2-text` [CITED: developmentseed.org/tipg/user_guide/endpoints]
- **Nullable geometry:** TiPG discovers tables with geometry columns regardless of NULL values. Features with NULL geometry return `"geometry": null` in GeoJSON (PostGIS 3.5.7 fix). Tiles skip NULL-geometry rows. [CITED: postgis.net ticket #5597 + TiPG factory.py source]

### Pattern 4: Celery Bulk Ingestion with Sync psycopg
**What:** Celery task that reads .xls with xlrd, transforms rows to ORM objects, and bulk-inserts via sync SQLAlchemy session.
**When to use:** When ingesting spreadsheet data into PostgreSQL in background.
**Example:**
```python
# Source: SQLAlchemy 2.0 docs + geospatial-api.com Celery bulk upload guide
# + celery.school SQLAlchemy session handling

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from api.config.settings import settings
from api.models.structure import StructureModel, StructureFactModel
from api.models.provenance import ProvenanceModel
import xlrd

@celery_app.task(bind=True, name="ingest_kazvodhoz")
def ingest_kazvodhoz_task(self, filepath: str = "датасет.xls", force: bool = False):
    """Ingest Kazvodhoz spreadsheet into PostGIS.

    Uses sync psycopg connection for efficient bulk loading.
    Idempotent: checks source_reference in provenance before inserting.
    """
    engine = create_engine(settings.sync_database_url)
    
    with Session(engine) as session:
        # 1. Read spreadsheet
        wb = xlrd.open_workbook(filepath)
        sheet = wb.sheet_by_name("Корректировка")
        
        # 2. Parse data rows (skip headers, group/category rows, summary rows)
        records = parse_kazvodhoz_sheet(sheet)
        
        # 3. Cross-reference with other sheets for additional columns
        sheet_kanaly = wb.sheet_by_name("каналы")
        sheet_list1 = wb.sheet_by_name("Лист1")
        records = enrich_with_cross_sheet_data(records, sheet_kanaly, sheet_list1)
        
        inserted = 0
        skipped = 0
        
        for record in records:
            # 4. Idempotency check (D-19)
            source_ref = f"датасет.xls:Корректировка:row:{record['row_num']}"
            existing = session.execute(
                select(ProvenanceModel).where(
                    ProvenanceModel.source_reference == source_ref
                )
            ).scalar_one_or_none()
            
            if existing and not force:
                skipped += 1
                continue
            
            # 5. Create provenance (D-20)
            provenance = ProvenanceModel(
                source_type="kazvodhoz_spreadsheet",
                source_reference=source_ref,
                confidence_level="HIGH",
                contributor="system:ingestion",
            )
            session.add(provenance)
            session.flush()  # Get provenance.id
            
            # 6. Create structure with NULL geometry (D-02)
            structure = StructureModel(
                name_ru=str(record.get("name", "")),
                type="canal",  # D-09
                geometry=None,  # D-02 — no coordinates in spreadsheet
                provenance_id=provenance.id,
                # Denormalized filterable columns (D-08)
                district=record.get("district"),
                water_source=record.get("water_source"),
                technical_condition=record.get("technical_condition"),
                wear_percentage=record.get("wear_percentage"),
                commissioning_year=record.get("commissioning_year"),
                cadastral_number=record.get("cadastral_number"),
                structure_count=record.get("structure_count"),
            )
            session.add(structure)
            session.flush()  # Get structure.id
            
            # 7. Create structure_facts for each column (D-07)
            for attr_name, attr_value in record["facts"].items():
                fact = StructureFactModel(
                    structure_id=structure.id,
                    attribute_name=attr_name,
                    attribute_value={"value": attr_value},
                    provenance_id=provenance.id,
                )
                session.add(fact)
            
            inserted += 1
        
        session.commit()
    
    engine.dispose()
    return {"inserted": inserted, "skipped": skipped, "total": len(records)}
```

### Pattern 5: FastAPI Structure CRUD Route (following provenance pattern)
**What:** REST endpoints for structures following the existing provenance route/service/model pattern.
**When to use:** For all /api/v1/structures endpoints.
**Example:**
```python
# Source: Existing provenance.py route pattern + FastAPI docs pagination patterns

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
import uuid

router = APIRouter(prefix="/api/v1", tags=["structures"])

class StructureResponse(BaseModel):
    """Response model for a structure record."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name_ru: str | None
    name_kk: str | None
    name_en: str | None
    type: str
    district: str | None
    water_source: str | None
    technical_condition: str | None
    wear_percentage: float | None
    commissioning_year: int | None
    cadastral_number: str | None
    structure_count: int | None
    # geometry as GeoJSON or WKT string
    geometry: dict | None = None
    provenance_id: uuid.UUID

class StructureListResponse(BaseModel):
    """Paginated list response with total count."""
    items: list[StructureResponse]
    total: int
    offset: int
    limit: int

@router.get("/structures", response_model=StructureListResponse)
async def list_structures(
    type: str | None = None,
    district: str | None = None,
    technical_condition: str | None = None,
    water_source: str | None = None,
    q: str | None = Query(None, description="Full-text + fuzzy search query"),
    lang: Literal["ru", "kk", "en"] = "ru",
    bbox: str | None = Query(None, description="minx,miny,maxx,maxy"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    format: Literal["json", "geojson"] = "json",
):
    """List structures with filtering, search, and pagination."""
    # Service layer handles query construction
    ...

@router.get("/structures/search", response_model=StructureListResponse)
async def search_structures(
    q: str = Query(..., description="Search query"),
    lang: Literal["ru", "kk", "en"] = "ru",
    type: str | None = None,
    district: str | None = None,
    condition: str | None = None,
    bbox: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    """Search structures using FTS + trigram fuzzy matching (D-12)."""
    ...
```

### Anti-Patterns to Avoid
- **Don't use async SQLAlchemy for bulk ingestion:** Async session overhead is significant for 444×22 = ~10K row inserts. Use sync psycopg via `sync_database_url`. [CITED: geospatial-api.com]
- **Don't hand-roll GeoJSON serialization:** Use PostGIS `ST_AsGeoJSON` or GeoAlchemy2's built-in GeoJSON support. Manual serialization misses CRS, NULL geometry, and edge cases. [CITED: postgis.net docs]
- **Don't use expression indexes for tsvector:** Generated columns with GIN indexes are simpler and faster than expression indexes (`CREATE INDEX ... ON table USING GIN (to_tsvector(...))`). Generated columns don't require specifying config in every query. [CITED: postgresql.org/docs/current/textsearch-tables.html]
- **Don't create GiST trigram indexes for filter-only queries:** GIN is faster for `WHERE col % 'query'` patterns. GiST is only needed for `ORDER BY col <-> 'query'` KNN queries. [CITED: postgresql.org/docs/current/pgtrgm.html]
- **Don't skip the cross-sheet data enrichment:** 'Корректировка' sheet alone has only 13 of 22 columns. The filterable columns (district, wear%, condition, cadastral) are in 'каналы' and 'Лист1'. Ingesting only 'Корректировка' would leave filterable columns NULL. [VERIFIED: spreadsheet analysis]
- **Don't use `TIPG_DATABASE_URL` as the env var name:** TiPG uses `DATABASE_URL` (Starlette config pattern), not a prefixed variable. [CITED: developmentseed.org/tipg/user_guide/configuration]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OGC API Features/Tiles server | Custom FastAPI endpoints for OGC compliance | TiPG container (pure config) | TiPG handles OGC spec compliance, CQL2 parsing, MVT generation, TileJSON/StyleJSON. Building this custom would be weeks of work and likely non-compliant. |
| .xls file parsing | Custom binary format parser | xlrd 2.0.2 | xlrd handles BIFF format, cell types, date conversion, encoding. Only library that reads .xls. |
| Full-text search ranking | Custom text matching algorithm | PostgreSQL ts_rank_cd + generated tsvector | FTS is built into PostgreSQL with language-specific stemming, stop words, ranking. Custom solutions miss edge cases. |
| Fuzzy string matching | Levenshtein distance implementation | pg_trgm similarity() + % operator | pg_trgm is a PostgreSQL extension with GIN/GiST index support. Custom Python-side matching can't use database indexes. |
| Vector tile generation | Custom MVT encoding | TiPG (uses PostGIS ST_AsMVT) | ST_AsMVT is PostGIS's native MVT generator. TiPG wraps it with OGC API Tiles spec compliance. |
| Bulk insert optimization | Row-by-row async insert | SQLAlchemy 2.0 session.execute(insert(Model), values) with sync psycopg | Batch inserts are 10-100x faster than row-by-row. Sync avoids async overhead for bulk operations. |
| Idempotent ingestion | External tracking table | PostgreSQL ON CONFLICT or pre-check on source_reference | Database-level idempotency is atomic and reliable. External tracking has race conditions. |
| GeoJSON response formatting | Manual dict construction | PostGIS ST_AsGeoJSON or GeoAlchemy2 | Handles NULL geometry, CRS, coordinate precision correctly. PostGIS 3.5.7 fixes NULL geometry output. |

**Key insight:** Every problem in this phase has a mature, standards-compliant solution. The phase is primarily about configuration and wiring, not algorithm development. The planner should focus on integration patterns, not custom implementations.

## Runtime State Inventory

> This is a greenfield data ingestion phase (no rename/refactor). However, the schema change (nullable geometry) modifies an existing table from Phase 1.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — Phase 1 created schema but ingested no structure records. The `structures` table is empty. | No data migration needed. Migration 0002 alters schema only. |
| Live service config | Docker Compose has 5 services (postgres, redis, minio, api, celery-worker). TiPG is NOT yet configured. | Add TiPG as 6th service in docker-compose.yml. Add `DATABASE_URL` env var for TiPG. |
| OS-registered state | None — no OS-level registrations. | None. |
| Secrets/env vars | `.env.example` has API_* vars but no TiPG config. `init-extensions.sql` already has `CREATE EXTENSION pg_trgm`. | Add TiPG connection vars to `.env.example`. pg_trgm already enabled — no action needed. |
| Build artifacts | None — no compiled binaries or installed packages with old names. | None. |

**Nothing found in categories:** Stored data (empty table), OS-registered state (none), Build artifacts (none). Verified by inspecting docker-compose.yml, init-extensions.sql, .env.example, and the empty structures table.

## Common Pitfalls

### Pitfall 1: xlrd Cell Type Handling — Numbers as Floats
**What goes wrong:** xlrd returns all numeric cells as Python floats. Year "1973" becomes `1973.0`, row number "1" becomes `1.0`. If you store these directly, database integer columns get `1973.0` instead of `1973`.
**Why it happens:** xlrd's `cell_value()` returns float for `XL_CELL_NUMBER` (ctype=2). There's no integer type in .xls format.
**How to avoid:** Convert floats to int when the value is a whole number: `int(val) if val == int(val) else val`. Check `cell.ctype` before processing. For years: `int(sheet.cell_value(row, 2))` if ctype is 2. For text columns (water source, district), ctype should be 1 (XL_CELL_TEXT) — but some cells may be empty (ctype=0).
**Warning signs:** Commissioning year stored as `1973.0` in database. Structure count as `20.0`. Filter queries on integer columns failing due to type mismatch.

### Pitfall 2: Spreadsheet Row Structure — Hidden Header and Summary Rows
**What goes wrong:** The spreadsheet has multi-row headers (rows 0-5), a column-number indicator row (row 6 with values 1.0, 2.0, 3.0...), interspersed category/group header rows ("Категория объектов", "Группа объектов 1/2/3"), and summary rows at the bottom (rows 442-443 with aggregate totals). Naively iterating all rows will insert header text and totals as data records.
**Why it happens:** The spreadsheet was designed for human reading, not machine ingestion. Group headers divide data into ownership categories. Summary rows show totals.
**How to avoid:** Skip rows where col 0 is non-numeric (text like "Категория объектов", "Группа объектов"). Skip rows 0-6 (headers + column number row). Skip the last 2-3 rows (summary totals). Use the № column (col 0) as the primary data row indicator — if it's a float > 0 and < 500, it's likely a data row.
**Warning signs:** Structure names like "Категория объектов" or "Группа объектов 1" appearing in the database. Summary totals (833.33 km, 2740.95 km) appearing as individual structure records. Record count > 444.

### Pitfall 3: 'Корректировка' Sheet Has Only 13 of 22 Columns
**What goes wrong:** D-18 says to read from 'Корректировка' sheet, but this sheet has only 13 columns. The filterable columns needed for D-08 (district, water_source, technical_condition, wear_percentage, commissioning_year, cadastral_number, structure_count) are NOT in 'Корректировка' — they're in 'каналы' (22 cols) and 'Лист1' (19 cols). Ingesting only 'Корректировка' leaves all filterable columns NULL.
**Why it happens:** 'Корректировка' is a "correction" sheet with before/after reconstruction data and notes, not the full dataset.
**How to avoid:** Cross-reference all three sheets using col 0 (№) as join key. Read primary data from 'Корректировка' (lengths, capacity, notes). Enrich with 'каналы' (district, rural district, wear%, condition, cadastral, state act) and 'Лист1' (canal parameters, structure count, year accepted). This is explicitly mentioned in D-18: "Cross-reference between sheets using the row number as join key."
**Warning signs:** All `district`, `technical_condition`, `wear_percentage` values are NULL after ingestion. Search and filter endpoints return empty results. TiPG collection has no filterable properties.

### Pitfall 4: TiPG Environment Variable Name — DATABASE_URL not TIPG_DATABASE_URL
**What goes wrong:** CONTEXT.md D-06 mentions `TIPG_DATABASE_URL` as the env var name. TiPG actually uses `DATABASE_URL` (Starlette config pattern) or individual `POSTGRES_USER`, `POSTGRES_PASS`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DBNAME` vars.
**Why it happens:** CONTEXT.md was written before TiPG docs were checked. The `TIPG_` prefix applies to application-level settings (TIPG_CORS_ORIGIN, TIPG_DEFAULT_FEATURES_LIMIT, etc.), not the database connection.
**How to avoid:** Use `DATABASE_URL` for the database connection in docker-compose.yml. Use `TIPG_*` prefixed vars for TiPG application settings.
**Warning signs:** TiPG container starts but can't connect to database. Error: "DATABASE_URL not set" or connection refused.

### Pitfall 5: Generated tsvector Column Immutability — Can't Use Column as Config Name
**What goes wrong:** Attempting to use a column value as the FTS configuration name in a generated column: `GENERATED ALWAYS AS (to_tsvector(language_col::regconfig, text)) STORED` fails with "generation expression is not immutable" error.
**Why it happens:** PostgreSQL requires generated column expressions to be immutable. Casting a column to `regconfig` is not immutable because the column value could change.
**How to avoid:** Use fixed config names in each generated column: `to_tsvector('russian', ...)`, `to_tsvector('simple', ...)`, `to_tsvector('english', ...)`. Create separate columns per language (D-10 already specifies this approach). If dynamic language is needed, use a trigger instead of a generated column.
**Warning signs:** Alembic migration fails with "generation expression is not immutable" error.

### Pitfall 6: NULL Geometry and TiPG Spatial Extent Calculation
**What goes wrong:** TiPG calculates spatial extent (bbox) for collection metadata. When ALL geometries are NULL (as in our case after Phase 2 ingestion), the spatial extent may be empty or cause errors in the `/collections` response.
**Why it happens:** `TIPG_DB_SPATIAL_EXTENT=True` (default) makes TiPG compute `ST_Extent(geometry)` for each collection. With all NULL geometries, `ST_Extent` returns NULL.
**How to avoid:** Set `TIPG_DB_SPATIAL_EXTENT=False` if all geometries are NULL, OR accept that the collection will show empty spatial extent (which is valid per OGC spec). Once Phase 4 assigns coordinates, the extent will populate automatically. The Features API still works — items are returned with `"geometry": null`. Tiles will return empty tiles (no features to render).
**Warning signs:** `/collections` endpoint returns errors or empty bbox. QGIS can connect but shows no features on the map. This is EXPECTED behavior for Phase 2 — all geometries are NULL by design (D-02).

### Pitfall 7: Alembic Migration — DROP NOT NULL on Geometry Column
**What goes wrong:** The Phase 1 migration created `geometry` with `nullable=False`. The Alembic migration to make it nullable must use `ALTER TABLE structures ALTER COLUMN geometry DROP NOT NULL`, not `op.alter_column()` with `nullable=True` (which may try to recreate the column and lose the GiST index).
**Why it happens:** GeoAlchemy2 Geometry columns have special handling. `op.alter_column()` may not correctly handle PostGIS geometry type modifications.
**How to avoid:** Use `op.execute("ALTER TABLE structures ALTER COLUMN geometry DROP NOT NULL")` for the nullable change. The existing GiST spatial index remains valid after dropping NOT NULL.
**Warning signs:** Migration fails, GiST index is dropped, or geometry column type is lost.

## Code Examples

### Spreadsheet Parsing with xlrd (handling multi-row headers)
```python
# Source: xlrd 2.0.2 official docs (xlrd.readthedocs.io) + spreadsheet analysis

import xlrd

def parse_kazvodhoz_sheet(sheet: xlrd.sheet.Sheet) -> list[dict]:
    """Parse the 'Корректировка' sheet, skipping headers and summary rows.
    
    Sheet structure (444 total rows):
    - Rows 0-4: Multi-row headers (title, subtitle, column headers, sub-headers)
    - Row 5: Sub-header continuation ('землян., км', 'облицов., км')
    - Row 6: Column number indicator (1.0, 2.0, 3.0...) — NOT data, SKIP
    - Row 7: 'Категория объектов' — category header, SKIP
    - Row 8: 'Группа объектов 1' — group header, SKIP
    - Rows 9-72: Data for Group 1
    - Row 73: 'Группа объектов 2' — group header, SKIP
    - Rows 74-209: Data for Group 2
    - Row 210: 'Группа объектов 3' — group header, SKIP
    - Rows 211-441: Data for Group 3
    - Rows 442-443: Summary totals, SKIP
    
    Total data rows: ~434 (not 444 — 444 is the total row count including headers)
    """
    records = []
    
    for row_idx in range(7, sheet.nrows):  # Start after column number row
        col0 = sheet.cell_value(row_idx, 0)
        
        # Skip non-data rows: group/category headers, summary rows
        if not isinstance(col0, float) or col0 < 1 or col0 > 500:
            continue
        
        # Skip summary rows (large aggregate values in col 0)
        if col0 > 440:  # Summary rows have col0 values like 229.0, 427.0
            # Check if this is a summary by looking at col 1 (name)
            col1 = sheet.cell_value(row_idx, 1)
            if not col1 or str(col1).strip() == "":
                continue
        
        record = {
            "row_num": int(col0),
            "name": str(sheet.cell_value(row_idx, 1)) if sheet.cell_value(row_idx, 1) else None,
            "commissioning_year": int(sheet.cell_value(row_idx, 2)) if sheet.cell_value(row_idx, 2) else None,
            "water_source": str(sheet.cell_value(row_idx, 3)) if sheet.cell_value(row_idx, 3) else None,
            "capacity_m3s": float(sheet.cell_value(row_idx, 4)) if sheet.cell_value(row_idx, 4) else None,
            "total_length_before_km": float(sheet.cell_value(row_idx, 5)) if sheet.cell_value(row_idx, 5) else None,
            "earthwork_length_km": float(sheet.cell_value(row_idx, 6)) if sheet.cell_value(row_idx, 6) else None,
            "lined_length_km": float(sheet.cell_value(row_idx, 7)) if sheet.cell_value(row_idx, 7) else None,
            "total_length_after_km": float(sheet.cell_value(row_idx, 9)) if sheet.cell_value(row_idx, 9) else None,
            "notes": str(sheet.cell_value(row_idx, 12)) if sheet.cell_value(row_idx, 12) else None,
        }
        records.append(record)
    
    return records
```

### Cross-Sheet Data Enrichment
```python
# Source: Spreadsheet analysis — 3 sheets with different column counts

def enrich_with_cross_sheet_data(records: list[dict], sheet_kanaly, sheet_list1) -> list[dict]:
    """Enrich 'Корректировка' records with data from 'каналы' and 'Лист1' sheets.
    
    'каналы' (22 cols) has: district (col 15), rural_district (col 16), 
    wear_percentage (col 17), technical_condition (col 18), 
    cadastral_number (col 19), state_act (col 20)
    
    'Лист1' (19 cols) has: district (col 13), wear_percentage (col 14),
    technical_condition (col 15), canal_parameters (col 16),
    structure_count (col 17), year_accepted (col 18)
    
    Join key: col 0 (№) — the row number, consistent across all sheets.
    """
    # Build lookup by row number
    kanaly_lookup = {}
    for r in range(5, sheet_kanaly.nrows):
        col0 = sheet_kanaly.cell_value(r, 0)
        if isinstance(col0, float) and 1 <= col0 <= 440:
            kanaly_lookup[int(col0)] = {
                "district": str(sheet_kanaly.cell_value(r, 15)) if sheet_kanaly.cell_value(r, 15) else None,
                "rural_district": str(sheet_kanaly.cell_value(r, 16)) if sheet_kanaly.cell_value(r, 16) else None,
                "wear_percentage": float(sheet_kanaly.cell_value(r, 17)) if sheet_kanaly.cell_value(r, 17) else None,
                "technical_condition": str(sheet_kanaly.cell_value(r, 18)) if sheet_kanaly.cell_value(r, 18) else None,
                "cadastral_number": str(sheet_kanaly.cell_value(r, 19)) if sheet_kanaly.cell_value(r, 19) else None,
                "state_act": str(sheet_kanaly.cell_value(r, 20)) if sheet_kanaly.cell_value(r, 20) else None,
            }
    
    list1_lookup = {}
    for r in range(5, sheet_list1.nrows):
        col0 = sheet_list1.cell_value(r, 0)
        if isinstance(col0, float) and 1 <= col0 <= 440:
            list1_lookup[int(col0)] = {
                "structure_count": int(sheet_list1.cell_value(r, 17)) if sheet_list1.cell_value(r, 17) else None,
                "year_accepted": int(sheet_list1.cell_value(r, 18)) if sheet_list1.cell_value(r, 18) else None,
                "canal_parameters": str(sheet_list1.cell_value(r, 16)) if sheet_list1.cell_value(r, 16) else None,
            }
    
    for record in records:
        row_num = record["row_num"]
        # Prefer 'каналы' for filterable columns (has all 22 columns)
        kanaly_data = kanaly_lookup.get(row_num, {})
        list1_data = list1_lookup.get(row_num, {})
        
        record["district"] = kanaly_data.get("district") or list1_data.get("district")
        record["water_source"] = record.get("water_source")  # Already from Корректировка
        record["technical_condition"] = kanaly_data.get("technical_condition") or list1_data.get("technical_condition")
        record["wear_percentage"] = kanaly_data.get("wear_percentage") or list1_data.get("wear_percentage")
        record["commissioning_year"] = record.get("commissioning_year")  # Already from Корректировка
        record["cadastral_number"] = kanaly_data.get("cadastral_number")
        record["structure_count"] = list1_data.get("structure_count")
        record["rural_district"] = kanaly_data.get("rural_district")
        record["canal_parameters"] = list1_data.get("canal_parameters")
    
    return records
```

### Alembic Migration 0002 — Schema Changes
```python
# Source: PostgreSQL docs for generated columns + pg_trgm + existing 0001 migration pattern

"""add filterable columns, generated tsvector, trigram indexes, nullable geometry

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002"
down_revision: str | None = "0001"

def upgrade() -> None:
    # 1. Make geometry nullable (D-02) — use raw SQL to preserve GiST index
    op.execute("ALTER TABLE structures ALTER COLUMN geometry DROP NOT NULL")
    
    # 2. Add filterable denormalized columns (D-08)
    op.add_column("structures", sa.Column("district", sa.String(255), nullable=True))
    op.add_column("structures", sa.Column("water_source", sa.String(255), nullable=True))
    op.add_column("structures", sa.Column("technical_condition", sa.String(100), nullable=True))
    op.add_column("structures", sa.Column("wear_percentage", sa.Float, nullable=True))
    op.add_column("structures", sa.Column("commissioning_year", sa.Integer, nullable=True))
    op.add_column("structures", sa.Column("cadastral_number", sa.String(255), nullable=True))
    op.add_column("structures", sa.Column("structure_count", sa.Integer, nullable=True))
    
    # 3. B-tree indexes on filterable columns
    op.create_index("ix_structures_district", "structures", ["district"])
    op.create_index("ix_structures_water_source", "structures", ["water_source"])
    op.create_index("ix_structures_technical_condition", "structures", ["technical_condition"])
    op.create_index("ix_structures_type", "structures", ["type"])
    
    # 4. Generated tsvector columns for multilingual FTS (D-10)
    op.execute("""
        ALTER TABLE structures ADD COLUMN search_ts_ru tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('russian', coalesce(name_ru, '')), 'A') ||
            setweight(to_tsvector('russian', coalesce(district, '')), 'B') ||
            setweight(to_tsvector('russian', coalesce(water_source, '')), 'B') ||
            setweight(to_tsvector('russian', coalesce(technical_condition, '')), 'C')
        ) STORED
    """)
    op.execute("""
        ALTER TABLE structures ADD COLUMN search_ts_kk tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('simple', coalesce(name_kk, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(district, '')), 'B')
        ) STORED
    """)
    op.execute("""
        ALTER TABLE structures ADD COLUMN search_ts_en tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(name_en, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(district, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(water_source, '')), 'B')
        ) STORED
    """)
    
    # 5. GIN indexes on tsvector columns
    op.execute("CREATE INDEX ix_structures_search_ts_ru ON structures USING GIN (search_ts_ru)")
    op.execute("CREATE INDEX ix_structures_search_ts_kk ON structures USING GIN (search_ts_kk)")
    op.execute("CREATE INDEX ix_structures_search_ts_en ON structures USING GIN (search_ts_en)")
    
    # 6. GIN trigram indexes for fuzzy matching (D-11)
    # pg_trgm already enabled in init-extensions.sql
    op.execute("CREATE INDEX ix_structures_name_ru_trgm ON structures USING GIN (name_ru gin_trgm_ops)")
    op.execute("CREATE INDEX ix_structures_name_kk_trgm ON structures USING GIN (name_kk gin_trgm_ops)")
    op.execute("CREATE INDEX ix_structures_name_en_trgm ON structures USING GIN (name_en gin_trgm_ops)")

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_structures_name_en_trgm")
    op.execute("DROP INDEX IF EXISTS ix_structures_name_kk_trgm")
    op.execute("DROP INDEX IF EXISTS ix_structures_name_ru_trgm")
    op.execute("DROP INDEX IF EXISTS ix_structures_search_ts_en")
    op.execute("DROP INDEX IF EXISTS ix_structures_search_ts_kk")
    op.execute("DROP INDEX IF EXISTS ix_structures_search_ts_ru")
    op.execute("ALTER TABLE structures DROP COLUMN IF EXISTS search_ts_en")
    op.execute("ALTER TABLE structures DROP COLUMN IF EXISTS search_ts_kk")
    op.execute("ALTER TABLE structures DROP COLUMN IF EXISTS search_ts_ru")
    op.drop_index("ix_structures_type", table_name="structures")
    op.drop_index("ix_structures_technical_condition", table_name="structures")
    op.drop_index("ix_structures_water_source", table_name="structures")
    op.drop_index("ix_structures_district", table_name="structures")
    op.drop_column("structures", "structure_count")
    op.drop_column("structures", "cadastral_number")
    op.drop_column("structures", "commissioning_year")
    op.drop_column("structures", "wear_percentage")
    op.drop_column("structures", "technical_condition")
    op.drop_column("structures", "water_source")
    op.drop_column("structures", "district")
    op.execute("ALTER TABLE structures ALTER COLUMN geometry SET NOT NULL")
```

### FastAPI bbox Spatial Filtering
```python
# Source: PostGIS ST_MakeEnvelope + ST_Intersects pattern + GeoAlchemy2

from geoalchemy2 import functions as geofunc
from sqlalchemy import select, func, and_

async def list_structures_with_bbox(
    session, bbox: str | None, filters: dict, offset: int, limit: int
):
    """List structures with optional bbox spatial filter."""
    stmt = select(StructureModel)
    
    # Apply attribute filters
    if filters.get("type"):
        stmt = stmt.where(StructureModel.type == filters["type"])
    if filters.get("district"):
        stmt = stmt.where(StructureModel.district == filters["district"])
    
    # Apply bbox spatial filter (minx,miny,maxx,maxy)
    if bbox:
        parts = [float(x) for x in bbox.split(",")]
        if len(parts) == 4:
            envelope = func.ST_MakeEnvelope(parts[0], parts[1], parts[2], parts[3], 4326)
            stmt = stmt.where(
                and_(
                    StructureModel.geometry.isnot(None),  # Skip NULL geometry
                    geofunc.ST_Intersects(StructureModel.geometry, envelope)
                )
            )
    
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar()
    
    # Paginate
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    
    return items, total
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Trigger-based tsvector updates | Generated tsvector columns (PG 12+) | PostgreSQL 12 (2019) | No trigger maintenance, auto-updates on INSERT/UPDATE, simpler schema |
| `set_limit()` for pg_trgm threshold | `SET pg_trgm.similarity_threshold` | PostgreSQL 9.6 | `set_limit()` deprecated; use configuration parameter instead |
| `ST_AsGeoJSON` with NULL geometry = `{"type": null}` | `ST_AsGeoJSON` with NULL geometry = `"geometry": null` | PostGIS 3.5.0 (2024) | Correct GeoJSON RFC compliance. We're on 3.5.7 — fix included. |
| next-pwa for PWA service workers | Serwist (bundler-agnostic) | 2024+ | Not relevant to Phase 2 but noted for frontend workstream |
| Custom OGC API server | TiPG (Development Seed) | 2023+ | Standards-compliant, auto-discovery, no custom code needed |

**Deprecated/outdated:**
- `set_limit()` function in pg_trgm: deprecated since PG 9.6, use `pg_trgm.similarity_threshold` config parameter
- `ST_AsGeoJSON` NULL geometry behavior: fixed in PostGIS 3.5.0 (we're on 3.5.7)
- Expression indexes for tsvector: superseded by generated columns in PG 12+ (simpler, no config specification needed in queries)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 'Корректировка' sheet has 434 data rows, not 444 (444 is total row count including headers) | Pitfall 2, Code Examples | If wrong, ingestion record count won't match requirement. Low risk — xlrd analysis confirmed row structure. |
| A2 | The join key (col 0, №) is consistent across all 3 sheets | Code Examples | If sheet numbering differs, cross-reference enrichment will produce NULL filterable columns. Medium risk — verified by spot-checking rows 1-10 in all sheets. |
| A3 | 'каналы' sheet column indices for filterable fields (district=15, wear=17, condition=18, etc.) are correct | Code Examples | If column indices are off, wrong data gets mapped to wrong fields. Medium risk — verified by examining header rows and data rows. |
| A4 | TiPG will discover the `structures` table even when all geometries are NULL | Pattern 3, Pitfall 6 | If TiPG requires non-NULL geometries for discovery, OGC API won't work until Phase 4. Low risk — TiPG discovers by column existence, not row values. |
| A5 | QGIS can connect to TiPG's OGC API Features endpoint without authentication | Success Criteria 2 | If auth is required, need to add auth middleware. Low risk — TiPG has no built-in auth, CORS is configurable. |
| A6 | `similarity_threshold` of 0.3 is appropriate for canal name fuzzy matching | Pattern 2 | If threshold too high, no matches returned. If too low, too many false positives. Low risk — configurable at query time, can be tuned. |

## Open Questions

1. **Should we add a `status` column for soft delete?**
   - What we know: D-13 mentions "soft delete via status field or hard delete". the agent's Discretion says this is open.
   - What's unclear: Whether the frontend needs to hide deleted structures or if hard delete is sufficient for Phase 2.
   - Recommendation: Add a `status` column (String, default 'active') in migration 0002. This is forward-looking — Phase 3 RBAC may need it. Hard delete loses provenance history.

2. **API response envelope format — plain list vs {data, meta}?**
   - What we know: Existing provenance endpoints return plain lists. D-16 mentions "Response includes total count for pagination UI."
   - What's unclear: Whether to return `{items: [...], total: N, offset: N, limit: N}` or add headers.
   - Recommendation: Use `{items: [...], total: N, offset: N, limit: N}` envelope for list/search endpoints (needed for pagination). Keep single-item endpoints as plain objects (matching provenance pattern).

3. **Should the ingestion endpoint accept file upload or only use the bundled file?**
   - What we know: D-15 says "accepts optional file upload (defaults to the bundled датасет.xls)".
   - What's unclear: Security implications of accepting file uploads.
   - Recommendation: Accept file upload but validate: file extension (.xls), file size (< 10MB), and use xlrd's built-in format validation. The bundled file is the default for convenience.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PostgreSQL 17 + PostGIS 3.5.7 | Data layer, TiPG | ✓ | 17 / 3.5.7 | — |
| Redis 7 | Celery broker | ✓ | 7-alpine | — |
| Docker Compose | All services | ✓ | latest | — |
| xlrd 2.0.2 | Spreadsheet parsing | ✓ | 2.0.2 | — |
| psycopg 3.2+ | Sync bulk insert | ✓ | 3.2+ (binary) | — |
| TiPG Docker image | OGC API | ✗ (not yet configured) | 1.3.1 | — (must add to docker-compose.yml) |
| pg_trgm extension | Fuzzy search | ✓ | built-in PG ext | — |
| curl (in containers) | Health checks | ✓ | — | — |

**Missing dependencies with no fallback:**
- TiPG container — must be added to docker-compose.yml. Image `ghcr.io/developmentseed/tipg:latest` available on GitHub Container Registry. [CITED: developmentseed.org/tipg]

**Missing dependencies with fallback:**
- None — all required dependencies are available or will be added in this phase.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | `apps/api/pyproject.toml` ([tool.pytest.ini_options]) |
| Quick run command | `cd apps/api && python -m pytest tests/ -x -q --timeout=30` |
| Full suite command | `cd apps/api && python -m pytest tests/ -v --timeout=60` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Spreadsheet ingestion into PostGIS with 444 records | unit | `pytest tests/test_ingestion.py::test_parse_kazvodhoz_sheet -x` | ❌ Wave 0 |
| DATA-01 | Ingestion creates provenance per structure | unit | `pytest tests/test_ingestion.py::test_provenance_creation -x` | ❌ Wave 0 |
| DATA-01 | Idempotent ingestion skips existing records | unit | `pytest tests/test_ingestion.py::test_idempotent_ingestion -x` | ❌ Wave 0 |
| DATA-01 | xlrd handles float-to-int conversion for years | unit | `pytest tests/test_ingestion.py::test_cell_type_handling -x` | ❌ Wave 0 |
| DATA-08 | FTS search returns ranked results | unit | `pytest tests/test_structures.py::test_fts_search -x` | ❌ Wave 0 |
| DATA-08 | pg_trgm fuzzy matching returns similar names | unit | `pytest tests/test_structures.py::test_fuzzy_search -x` | ❌ Wave 0 |
| DATA-08 | Combined FTS + trigram search blends scores | unit | `pytest tests/test_structures.py::test_combined_search -x` | ❌ Wave 0 |
| DATA-08 | Filter by district/condition/type works | unit | `pytest tests/test_structures.py::test_filter_structures -x` | ❌ Wave 0 |
| INT-01 | TiPG exposes structures as OGC API collection | integration | `pytest tests/test_tipg.py::test_ogc_collection_exists -x -m integration` | ❌ Wave 0 |
| INT-01 | CQL2 filtering works on TiPG items endpoint | integration | `pytest tests/test_tipg.py::test_cql2_filter -x -m integration` | ❌ Wave 0 |
| INT-03 | CRUD create returns 201 with structure | unit | `pytest tests/test_structures.py::test_create_structure -x` | ❌ Wave 0 |
| INT-03 | CRUD get by ID returns 200 or 404 | unit | `pytest tests/test_structures.py::test_get_structure -x` | ❌ Wave 0 |
| INT-03 | List with pagination returns total count | unit | `pytest tests/test_structures.py::test_list_pagination -x` | ❌ Wave 0 |
| INT-03 | bbox spatial filter works | integration | `pytest tests/test_structures.py::test_bbox_filter -x -m integration` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd apps/api && python -m pytest tests/ -x -q --timeout=30`
- **Per wave merge:** `cd apps/api && python -m pytest tests/ -v --timeout=60`
- **Phase gate:** Full suite green + integration tests (with Docker stack) green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `apps/api/tests/test_structures.py` — covers DATA-08, INT-03 (CRUD, search, filter)
- [ ] `apps/api/tests/test_ingestion.py` — covers DATA-01 (parsing, idempotency, provenance)
- [ ] `apps/api/tests/test_tipg.py` — covers INT-01 (OGC API collection, CQL2) — integration marker
- [ ] `apps/api/tests/conftest.py` — add structure fixtures, mock spreadsheet data
- [ ] Framework install: `xlrd` already installed; no additional framework needed

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth in Phase 2 (RBAC deferred to Phase 3). TiPG has no built-in auth. |
| V3 Session Management | no | No sessions in Phase 2. |
| V4 Access Control | no | No RBAC in Phase 2. All endpoints are open. Document as technical debt for Phase 3. |
| V5 Input Validation | yes | Pydantic models validate all API request bodies. Query params typed with Literal/Field constraints. File upload validated (extension, size). |
| V6 Cryptography | no | No encryption needed in Phase 2. |
| V7 Error Handling | yes | Global exception handler exists (Phase 1). HTTPException for 404/400. Structured error responses. |
| V8 Data Protection | yes | Provenance tracking on all data (DATA-07). No PII in spreadsheet (anonymized data). |
| V9 Communications | yes | CORS configured (Phase 1). HTTPS handled by reverse proxy in production. |
| V12 Files & Resources | yes | File upload validation for ingestion endpoint. xlrd parsing is safe (no macro execution). |

### Known Threat Patterns for FastAPI + PostgreSQL + PostGIS Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via search query | Tampering | Use SQLAlchemy ORM parameterized queries. Never string-interpolate user input into SQL. Use `bindparam` for dynamic query construction. |
| PostGIS injection via bbox parameter | Tampering | Parse bbox to floats, validate 4 values, use `ST_MakeEnvelope` with parameterized values. Reject non-numeric input. |
| Malicious file upload | Tampering | Validate file extension (.xls only), file size (< 10MB), use xlrd's format detection. xlrd does not execute macros. |
| CQL2 injection via TiPG | Tampering | TiPG parses CQL2 using a proper parser (not string interpolation). CQL2 is a structured query language with defined grammar. [CITED: TiPG factory.py source] |
| Denial of service via large query results | DoS | `TIPG_MAX_FEATURES_PER_QUERY=10000` limits TiPG. FastAPI endpoints use `limit` parameter with max 1000. |
| Information disclosure via error messages | Information Disclosure | Global exception handler returns generic "Internal Server Error" for unhandled exceptions. Structured logging captures details server-side only. |

### Security Notes
- **No authentication in Phase 2:** All REST and OGC API endpoints are open. This is intentional — Phase 2 focuses on data layer functionality. Phase 3 adds RBAC (RISK-07). Document as accepted risk.
- **TiPG has no auth:** TiPG container exposes OGC API without authentication. In production, place behind a reverse proxy with auth. For development/demo, CORS + network isolation is sufficient.
- **Spreadsheet data is anonymized:** The current dataset uses placeholder values ("Район 1", "Сельский округ 1"). No PII risk. When real data replaces placeholders, review for PII and apply V8 controls.

## Sources

### Primary (HIGH confidence)
- TiPG official documentation — developmentseed.org/tipg/ (landing, configuration, endpoints, customization, features server)
- TiPG GitHub repository — github.com/developmentseed/tipg (docker-compose.yml, factory.py source)
- TiPG PyPI page — pypi.org/project/tipg/ (v1.3.1, Feb 2026)
- PostgreSQL official docs — postgresql.org/docs/current/ (textsearch-tables, textsearch-indexes, pgtrgm)
- PostGIS docs — postgis.net/docs/ (NULL geometry handling, ST_AsGeoJSON, geometry_columns view)
- PostGIS ticket #5597 — trac.osgeo.org/postgis/ticket/5597 (NULL geometry GeoJSON fix in 3.5.0)
- xlrd official docs — xlrd.readthedocs.io/ (API reference, cell types)
- xlrd PyPI — pypi.org/project/xlrd/ (v2.0.2, BSD license)
- Existing codebase — apps/api/ (models, routes, services, migrations, config, tests)

### Secondary (MEDIUM confidence)
- Multiple GitHub examples of generated tsvector columns — verified via grep_app search (simstudioai/sim, nextlevelbuilder/goclaw, iflytek/skillhub, eikek/docspell, swuecho/chat, ncarlier/readflow)
- pg_trgm fuzzy search guides — jamongx.com, mazeez.dev, goldlapel.com, fuzzy.website, pganalyze.com (all consistent with official docs)
- Celery SQLAlchemy session handling — celery.school
- Geospatial API bulk upload patterns — geospatial-api.com (psycopg2.extras.execute_values, page_size, transaction boundaries)
- PostgreSQL bulk load patterns — dev.to/de_clerke (COPY vs execute_values vs to_sql comparison)
- SQLAlchemy bulk insert discussion — github.com/sqlalchemy/sqlalchemy/discussions/10537 (session.execute(insert(Model), values) pattern)

### Tertiary (LOW confidence)
- None — all findings verified against official documentation or multiple credible sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified via pyproject.toml (installed), PyPI (versions), slopcheck (xlrd OK), official docs (TiPG)
- Architecture: HIGH — TiPG endpoints and configuration verified from official docs. Generated tsvector pattern verified from PostgreSQL docs + multiple GitHub examples. pg_trgm verified from official docs.
- Pitfalls: HIGH — spreadsheet analysis performed directly with xlrd. TiPG nullable geometry verified from PostGIS ticket + TiPG source code. Environment variable names verified from official config docs.
- Spreadsheet structure: HIGH — directly analyzed with xlrd, examined all 3 sheets, row counts, column mappings, header structures

**Research date:** 2026-06-26
**Valid until:** 2026-07-26 (30 days — stable technologies, no fast-moving dependencies)
