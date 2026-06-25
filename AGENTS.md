<!-- GSD:project-start source:PROJECT.md -->

## Project

**Zhambyl Hydraulic Structures Catalog**

A web-first, installable PWA that serves as the digital operating layer for hydraulic structures in Zhambyl Oblast, Kazakhstan. It ingests legacy registry data, discovers candidate structures from open sources and satellite imagery, compares them against the existing database, computes risk-informed inspection intervals and repair priorities, and gives inspectors and decision-makers a map-first, evidence-backed workflow. The system is trilingual (Russian, Kazakh, English) and designed for both office analytics and offline field use.

**Core Value:** Every hydraulic structure in Zhambyl has one canonical, evidence-backed record visible on an interactive map with its current condition, inspection urgency, and repair status — enabling data-driven maintenance decisions.

### Constraints

- **Tech stack**: Next.js PWA + MapLibre GL JS (frontend), FastAPI + PostgreSQL/PostGIS (backend), TiPG (vector tiles API), TiTiler + STAC/COG + MinIO (raster/imagery), Redis (caching/job queues), Milvus (vector similarity search), LangGraph (workflow orchestration) — chosen for standards compliance, demo reliability, and integration capability
- **Languages**: Trilingual UI required — Russian, Kazakh, English. Data sources are primarily in Russian.
- **Data sources**: Starting with Kazvodhoz spreadsheet only; OSM, satellite imagery, and other sources to be integrated during build
- **Standards**: OGC API Features/Tiles for vector access, STAC for EO metadata, S3-compatible MinIO for binary assets — required for integration deliverable
- **Architecture principle**: Every structure has one canonical asset record, many evidence sources, and a time-based condition history. PostGIS is the system of record. LLMs never make final engineering decisions.
- **Offline capability**: PWA with service workers for field inspection work without connectivity

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

### Frontend

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Next.js | 16.2.x | Full-stack React framework, PWA shell, SSR/SSG | Industry-leading React framework with built-in PWA manifest support, App Router, Server Components. Turbopack for fast builds. Official PWA guide covers manifest, service worker registration, offline. | HIGH |
| React | 19.x | UI library (bundled with Next.js 16) | Server Components, use() hook, Actions API. Required by Next.js 16. | HIGH |
| MapLibre GL JS | 5.19.x | Interactive WebGL map rendering, vector tiles | Open-source fork of Mapbox GL JS. GPU-accelerated vector tile rendering, 3D terrain, custom protocols. No proprietary license issues. The de facto open-source web map renderer. | HIGH |
| Serwist | latest (@serwist/next) | PWA service worker generation, offline caching | Officially recommended by Next.js PWA docs. Configurator mode is bundler-agnostic (works with Turbopack). Auto-precaches prerendered routes. Modern replacement for next-pwa. | MEDIUM |
| next-intl | 4.13.x | Trilingual i18n (Russian, Kazakh, English) | Purpose-built for Next.js App Router. ICU message format for plurals/rich text. Server Component support (zero client bundle for server translations). Type-safe. Internationalized routing with `[locale]` segment. 4.2K+ GitHub stars, actively maintained. | HIGH |
| TypeScript | 5.x | Type safety across frontend | Non-negotiable for a project of this complexity. Next.js 16 and MapLibre GL JS both ship first-class TypeScript types. | HIGH |
| Tailwind CSS | 4.x | Utility-first styling | Rapid UI development, consistent design system. Works with React Server Components. v4 uses CSS-native configuration. | HIGH |
| TanStack Query | 5.x | Server state management, data fetching/caching | Handles API data caching, background refetch, optimistic updates. Essential for offline-first PWA with deferred sync. Pairs with MapLibre for feature data fetching. | MEDIUM |
| Zustand | 5.x | Lightweight client state management | Map viewport state, UI panel state, offline queue state. Simpler than Redux for this scope. Used in real-world MapLibre projects. | MEDIUM |
| Dexie.js | 4.x | IndexedDB wrapper for offline data persistence | Field mode requires structured offline storage (captured inspections, photos metadata, sync queue). Dexie provides a clean Promise-based API over IndexedDB. Complements Serwist's asset caching. | MEDIUM |

### Backend

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| FastAPI | 0.128.x | Async Python API framework | High performance, automatic OpenAPI docs, type-hint-based validation. Lifespan context managers for startup/shutdown. Dependency injection with scopes (0.121+). The standard choice for Python geospatial APIs. | HIGH |
| Python | 3.12+ | Runtime | 3.12 has performance optimizations; 3.13+ adds more. TiPG requires >=3.11. Match TiPG's minimum or go higher. Avoid 3.13 edge cases with C extensions (GDAL). | HIGH |
| Uvicorn | 0.34+ | ASGI server | Standard FastAPI server. Use with Gunicorn in production (UvicornWorker). | HIGH |
| Pydantic | 2.x | Data validation, serialization | V2 is 5-50x faster than v1. Core to FastAPI. Use for all request/response models, domain DTOs. | HIGH |
| SQLAlchemy | 2.0+ | Async ORM, database abstraction | 2.0 has native async support (AsyncSession, async_engine). Declarative with Mapped type hints. Works with GeoAlchemy2 for PostGIS spatial types. | HIGH |
| GeoAlchemy2 | 0.18+ | PostGIS spatial types for SQLAlchemy | Adds Geometry, Geography, Raster types. Spatial functions via `func.ST_*`. Alembic-compatible. Required for type-safe PostGIS queries in ORM. | HIGH |
| asyncpg | 0.29+ | Async PostgreSQL driver | Fastest Python PostgreSQL driver. SQLAlchemy async backend (`postgresql+asyncpg://`). Built-in connection pooling. PostGIS geometry codec support. | HIGH |
| Alembic | 1.13+ | Database migrations | Standard SQLAlchemy migration tool. GeoAlchemy2 provides Alembic helpers for spatial index creation. | HIGH |
| Celery | 5.4+ | Distributed task queue for background jobs | Battle-tested, mature ecosystem (Flower monitoring, Beat scheduling). Handles OCR processing, data ingestion, tile pre-generation. Not async-native but reliable. See ARQ note below. | HIGH |
| Pydantic Settings | 2.x | Configuration management | Environment-based config with type validation. Pairs naturally with FastAPI. | HIGH |

### Database & Spatial

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PostgreSQL | 17.x | Primary database, system of record | 17 is current stable (18 in beta). PostGIS 3.5 supports PG 12-18. Use PostGIS Docker image (e.g., `postgis/postgis:17-3.5`) to get both bundled. | HIGH |
| PostGIS | 3.5.7 | Spatial extension — geometry, spatial indexing, ST_AsMVT | 3.5.7 released June 2026. Required by TiPG. Provides ST_AsMVT for vector tile generation, GiST spatial indexes, geography type for lat/lon. The system of record for all structure data. | HIGH |
| pgvector | 0.7+ | Vector similarity search within PostgreSQL | **RECOMMENDED OVER MILVUS FOR MVP.** Adds vector type + HNSW/IVFFlat indexing to PostgreSQL. Hybrid search via SQL: combine `tsvector @@ tsquery` (full-text) with `embedding <=> query_vector` (similarity) in one query. Zero new infrastructure. Sweet spot: 1-50M vectors — this project has thousands of structures and documents, well within range. See detailed rationale below. | HIGH |
| Redis | 7.x+ | Caching, Celery broker, session store | Multi-purpose: Celery message broker, API response cache, tile cache, rate limiting. Redis 7+ has significant performance gains. | HIGH |

### Geospatial Tile Serving

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| TiPG | 1.3.1 | OGC API Features + Tiles from PostGIS | **VALIDATED.** Provides both OGC API Features (CRUD for vector features) and OGC API Tiles (MVT generation from PostGIS). CQL2 filtering. TileJSON + StyleJSON endpoints for direct MapLibre integration. v1.3.1 (Feb 2026), actively maintained by Development Seed. FastAPI-based, shares the ecosystem. The project requires OGC API Features/Tiles — TiPG is purpose-built for this. | HIGH |
| TiTiler | latest | Dynamic raster tile server for COGs | **VALIDATED.** FastAPI-based, reads COGs from S3/MinIO with HTTP range requests. On-demand band math, color mapping, reprojection. STAC item support (MultiBaseTilerFactory + STACReader). No pre-tiling needed. Pairs with MinIO for satellite imagery serving. | HIGH |
| MinIO | latest | S3-compatible object storage | Stores COGs, STAC items, uploaded documents, photos, voice notes. S3 API compatible — TiTiler reads COGs via S3 range requests. Self-hosted, no cloud vendor lock-in. Also used as Milvus storage backend if Milvus is deployed. | HIGH |

### AI / Workflow

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| LangGraph | 1.0+ | Workflow orchestration, stateful agents | **VALIDATED.** Low-level orchestration framework for long-running, stateful workflows. Built-in checkpointing (MemorySaver for dev, PostgresSaver/RedisSaver for prod). Human-in-the-loop via `interrupt()` + `Command` — exactly matches the project's "human-in-the-loop review workflow for candidate verification." Retry policies, streaming, time travel. v1.0+ is the stable release line. | HIGH |
| LangChain | latest | LLM integration, document loaders, embeddings | LangGraph's companion library. Use for: document loaders (PDF, scanned images via OCR), text splitters, embedding models, LLM wrappers. Not for orchestration logic (that's LangGraph). | MEDIUM |
| pymilvus | 2.5+ | Milvus client (IF Milvus is used) | Only needed if Milvus is deployed. If using pgvector (recommended), use `pgvector` Python package instead. Milvus Lite (`pip install pymilvus`) provides embedded mode for prototyping with same API as Standalone — useful as middle ground. | MEDIUM |

### DevOps / Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Docker | latest | Containerization | Standard for all services. PostgreSQL/PostGIS, Redis, MinIO, TiPG, TiTiler, FastAPI, Celery workers — all containerized. | HIGH |
| Docker Compose | latest | Local dev + single-host deployment | 2-3 person team, single-region deployment. Compose is sufficient. K8s is premature for this stage. | HIGH |
| GitHub Actions | latest | CI/CD | Automated testing, linting, build, deploy. Free for public repos. | HIGH |

## Critical Decision: pgvector vs Milvus

### Recommendation: Use pgvector for MVP. Reassess Milvus if vector count exceeds ~50M.

- Vector count reliably exceeds 50M (unlikely for this project's scope)
- Need GPU-accelerated indexing
- Need Milvus's built-in BM25 sparse search with RRF reranking (though pgvector + tsvector achieves similar hybrid search)
- Milvus Lite (`pip install pymilvus`) is a zero-infrastructure middle ground if Milvus-specific features are wanted — embedded in-process, same API as Standalone for future migration

## Critical Decision: TiPG vs Martin for Vector Tiles

### Recommendation: Keep TiPG. It's the right choice.

- **Martin does NOT support OGC API Features.** It's tile-only. An open GitHub issue (#2365, Nov 2025) requests OGC API Features support; maintainers have no plans to implement it. The project explicitly requires "OGC API Features/Tiles for vector access" as an integration deliverable.
- **TiPG provides both OGC API Features AND Tiles.** It's the only lightweight option that does both from PostGIS. CQL2 filtering, TileJSON, StyleJSON — all directly consumable by MapLibre.
- **Performance is adequate at this scale.** ~1,400 structures is trivially small. TiPG's benchmark performance (ranked 5th of 6 servers) is still sub-second for this dataset size. Martin's speed advantage matters at millions of features, not thousands.
- **FastAPI ecosystem alignment.** TiPG is FastAPI-based, sharing the same Python ecosystem as the main API and TiTiler. Custom TiPG factories can be embedded in the main FastAPI app.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Vector search | **pgvector** | Milvus | Overkill for ~thousands of vectors. Adds infra complexity. Reassess at 50M+ vectors. |
| Vector search | **pgvector** | Milvus Lite | Viable middle ground if Milvus features needed. But pgvector is simpler (no separate process). |
| Vector tile server | **TiPG** | Martin | No OGC API Features support. Tile-only. Use as tile accelerator if needed later. |
| Vector tile server | **TiPG** | pg_tileserv | CrunchyData's minimal server. Only does tiles, not Features. Less actively maintained. |
| Vector tile server | **TiPG** | GeoServer | Heavyweight Java application. Legacy WMS/WFS focus. Overkill. Use only as fallback for legacy OGC clients. |
| Raster tile server | **TiTiler** | GeoServer | Same as above. TiTiler is purpose-built for COG/STAC dynamic tiling. |
| PWA service worker | **Serwist** | next-pwa | next-pwa is webpack-based, doesn't work with Turbopack. Older, less actively maintained. Serwist is officially recommended by Next.js docs. |
| PWA service worker | **Serwist** | Manual Workbox | More control but more boilerplate. Serwist wraps Workbox with Next.js-specific optimizations. |
| Job queue | **Celery** | ARQ | ARQ is in maintenance-only mode (no new features, no active development). Risk for new projects. |
| Job queue | **Celery** | Taskiq | Modern async-first alternative. Viable but smaller ecosystem. Consider if Celery's async bridge becomes painful. |
| Job queue | **Celery** | FastAPI BackgroundTasks | In-process only, no durability, tied to request lifecycle. Fine for fire-and-forget but not for OCR/ingestion pipelines. |
| Map renderer | **MapLibre GL JS** | Mapbox GL JS | Mapbox GL JS requires API key and has usage limits. MapLibre is the open-source fork, fully featured, no vendor lock-in. |
| Map renderer | **MapLibre GL JS** | OpenLayers | More powerful for complex GIS operations but heavier and less polished for vector tile rendering. MapLibre is the standard for modern vector tile web maps. |
| Map renderer | **MapLibre GL JS** | Leaflet | Simpler but no native vector tile rendering, no WebGL. Insufficient for this project's needs. |
| i18n | **next-intl** | react-i18next | react-i18next is not Next.js App Router native. next-intl has server component support, type safety, and is the de facto standard for Next.js. |
| ORM | **SQLAlchemy 2.0** | SQLModel | SQLModel is simpler but less mature, fewer features, and GeoAlchemy2 integration is less tested. SQLAlchemy 2.0 async is proven. |
| ORM | **SQLAlchemy 2.0** | Tortoise ORM | Async-native but much smaller ecosystem. No PostGIS extension equivalent to GeoAlchemy2. |

## Installation

### Frontend (Next.js PWA)

# Create Next.js 16 app

# Core UI

# State & data

# Styling (Tailwind v4 is built into create-next-app)

# Dev tools

### Backend (FastAPI + PostGIS)

# Core

# Database

# Geospatial

# Vector search (pgvector path)

# Job queue

# AI / Workflow

# Document processing

### Infrastructure (Docker Compose)

# docker-compose.yml — core services

## Architecture Note: Service Count

| Service | Image | Port | Notes |
|---------|-------|------|-------|
| PostgreSQL + PostGIS + pgvector | `postgis/postgis:17-3.5` | 5432 | System of record, vector search |
| Redis | `redis:7-alpine` | 6379 | Cache, Celery broker |
| MinIO | `minio/minio` | 9000/9001 | S3-compatible object storage |
| FastAPI API | custom | 8000 | Main REST API, auth, business logic |
| Celery Worker | custom | — | Background jobs (OCR, ingestion) |
| TiPG | `ghcr.io/developmentseed/tipg:latest` | 8080 | OGC API Features + Tiles |
| TiTiler | custom | 8081 | Dynamic raster tiling |
| Next.js | custom | 3000 | Frontend PWA |

## Version Verification Summary

| Technology | Verified Version | Source | Date Checked |
|------------|-----------------|--------|--------------|
| Next.js | 16.2.9 | Context7 | 2026-06-25 |
| MapLibre GL JS | 5.19.0 | Context7 | 2026-06-25 |
| FastAPI | 0.128.0 | Context7 | 2026-06-25 |
| PostGIS | 3.5.7 | Official postgis.net | 2026-06-25 |
| PostgreSQL | 17 (18 beta) | Official docs | 2026-06-25 |
| TiPG | 1.3.1 | PyPI | 2026-06-25 |
| TiTiler | latest (active dev) | Context7 / GitHub | 2026-06-25 |
| LangGraph | 1.0+ (1.0.8 in Context7) | Context7 | 2026-06-25 |
| Milvus | 2.5.x / 2.6.x | Context7 / official docs | 2026-06-25 |
| GeoAlchemy2 | 0.18.4 | Official docs | 2026-06-25 |
| next-intl | 4.13.0 | GitHub releases | 2026-06-25 |
| Serwist | latest | Official docs / npm | 2026-06-25 |

## Sources

- MapLibre GL JS: Context7 `/maplibre/maplibre-gl-js` (v5.19.0, 678 snippets, High reputation)
- FastAPI: Context7 `/fastapi/fastapi` (v0.128.0, 2153 snippets, High reputation)
- TiTiler: Context7 `/developmentseed/titiler` (1483 snippets, High reputation)
- LangGraph: Context7 `/websites/langchain_oss_python_langgraph` (1429 snippets, High reputation)
- Milvus: Context7 `/websites/milvus_io` (14189 snippets, High reputation)
- Next.js: Context7 `/vercel/next.js` (v16.2.9, 6064 snippets, High reputation)
- TiPG: Official docs https://developmentseed.org/tipg/ + PyPI https://pypi.org/project/tipg/ (v1.3.1, Feb 2026)
- Martin: GitHub https://github.com/maplibre/martin + benchmark https://github.com/FabianRechsteiner/vector-tiles-benchmark
- PostGIS: Official https://postgis.net/docs/manual-3.5/en/release_notes.html (3.5.7, June 2026)
- pgvector vs Milvus: Multiple sources including https://www.modern-datatools.com/compare/milvus-vs-pgvector (March 2026), DEV.to comparison (June 2026), Instaclustr, Zilliz blog
- Serwist: Official docs https://serwist.pages.dev/docs/next/config + Next.js PWA guide
- next-intl: GitHub https://github.com/amannn/next-intl (v4.13.0, May 2026)
- GeoAlchemy2: Official docs https://geoalchemy-2.readthedocs.io/ (v0.18.4)
- Celery vs ARQ: Multiple sources including bytay.dev (May 2026), Medium benchmarks (May 2026), Stackademic (April 2026)
- GeoLens (reference architecture): https://getgeolens.com/ (PostGIS + pgvector + MapLibre + TiTiler + FastAPI stack)
- eoAPI (reference architecture): Development Seed's eoAPI uses TiPG + TiTiler + STAC

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
