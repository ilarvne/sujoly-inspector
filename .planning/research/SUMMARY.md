# Project Research Summary

**Project:** Zhambyl Hydraulic Structures Catalog
**Domain:** Geospatial web portal / PWA for hydraulic infrastructure management (dam safety, water asset management)
**Researched:** 2026-06-25
**Confidence:** HIGH

## Executive Summary

The Zhambyl Hydraulic Structures Catalog is a geospatial PWA that serves as the "digital operating layer" for ~1,395 hydraulic structures in Zhambyl Oblast, Kazakhstan. Research across four dimensions — technology stack, feature landscape, architecture patterns, and pitfalls — converges on a clear picture: this is a PostGIS-centric geospatial platform with a dual API surface (standards-compliant OGC APIs via TiPG + business logic via FastAPI), an offline-first PWA for field inspection, and an evidence-grounded AI copilot. The reference architecture is well-established: Development Seed's eoAPI pattern (PgSTAC + stac-fastapi + titiler-pgstac + TiPG sharing one PostgreSQL) and GeoLens (PostGIS + pgvector + MapLibre + TiTiler + FastAPI) validate the exact combination this project needs. The domain is well-understood — commercial dam safety platforms (Dam360, DamData, KISTERS), academic Kazakhstan projects (kazdams.kz), and international risk frameworks (World Bank, FEMA/FERC) provide a mature feature landscape to draw from.

The recommended approach is a phased build that starts with infrastructure and data ingestion (the critical path), establishes the map and digital passport as the MVP, then layers on inspection lifecycle, evidence-fusion discovery, offline field mode, and AI copilot. Three stack adjustments from the original PROJECT.md are strongly warranted: **pgvector replaces Milvus** (both stack and pitfalls research independently reached this conclusion — the project has thousands of vectors, not millions, and pgvector eliminates 3+ Docker containers while enabling hybrid search in a single SQL query), **Serwist replaces next-pwa** (next-pwa is incompatible with Turbopack/Next.js 16), and **Celery replaces ARQ** (ARQ is in maintenance-only mode). Provenance tracking — originally a P2 feature — must be elevated to P1 and built into the initial data model, as it is the trust infrastructure that the AI copilot, matching taxonomy, and confidence scoring all depend on.

The key risks are domain-specific and well-documented. The #1 critical pitfall is Kazakhstan's coordinate system transition: QazTRF-23 (EPSG:10941) replaced Pulkovo 1942 on 2025-01-01, and the NTv2 grid file (`qazgrid_kz.gsb`) is not bundled with PROJ — getting this wrong places structures 50-200m from their real positions. The second major risk is PWA offline sync conflict resolution, which is the highest engineering complexity feature and the most likely to cause silent data loss in field operations. The third is TiPG's OGC API compliance gaps (no Features Part 2/CRS support, CITE test failures) which must be managed transparently with integration partners. Twenty-two domain-specific pitfalls have been documented with prevention strategies and phase assignments, giving the team a concrete risk map before implementation begins.

## Key Findings

### Recommended Stack

The proposed stack is fundamentally sound and aligns with the 2025/2026 geospatial web platform consensus. All versions have been verified against Context7, PyPI, and official documentation. Three adjustments are recommended; the rest are validated as correct. See [STACK.md](./STACK.md) for full rationale, version numbers, and alternatives analysis.

**Core technologies:**

- **Next.js 16 + React 19 + MapLibre GL JS 5**: Frontend PWA shell, interactive WebGL map rendering, vector tile display — the standard open-source web map stack
- **Serwist** (replaces next-pwa): PWA service worker generation — officially recommended by Next.js docs, bundler-agnostic for Turbopack compatibility
- **next-intl 4**: Trilingual i18n (RU/KK/EN) — purpose-built for Next.js App Router with Server Component support and type-safe ICU message format
- **FastAPI 0.128 + SQLAlchemy 2 + GeoAlchemy2**: Async Python API with type-safe PostGIS spatial types — the standard choice for Python geospatial APIs
- **PostgreSQL 17 + PostGIS 3.5 + pgvector**: System of record with spatial indexing and vector similarity search in one database — eliminates Milvus operational overhead
- **TiPG 1.3**: OGC API Features + Tiles directly from PostGIS — the only lightweight option that provides both; validated over Martin (tile-only, no OGC API Features)
- **TiTiler + MinIO**: Dynamic raster tile serving from COGs stored in S3-compatible object storage — no pre-tiling needed
- **Celery 5.4 + Redis 7**: Background task queue for OCR, ingestion, tile pre-generation — replaces ARQ (maintenance-only mode)
- **LangGraph 1.0**: Workflow orchestration with checkpointing and human-in-the-loop interrupts — exactly matches the project's candidate verification workflow
- **TanStack Query + Zustand + Dexie.js**: Client state management trio — server state caching, lightweight UI state, and IndexedDB for offline persistence

**Critical version requirements:** Pin PROJ >= 9.4 and GDAL >= 3.8 for QazTRF-23 support. Pin MapLibre GL JS to a version including PR #7590 (feature state performance fix, May 2026). Install `qazgrid_kz.gsb` NTv2 grid file in the PROJ data directory.

### Expected Features

Research surveyed 15+ commercial and academic dam safety / water asset management systems, international risk frameworks, AI copilot patterns, and PWA offline-first field collection platforms. The feature landscape is well-mapped with clear table stakes, differentiators, and anti-features. See [FEATURES.md](./FEATURES.md) for full analysis, dependency graph, and competitor matrix.

**Must have (table stakes — P1 MVP):**
- Interactive map with structure status visualization — the primary entry point; every competitor leads with a map
- Digital passport per structure — the canonical asset record; identity, type, geometry, specs, status, documents
- Structure inventory from Kazvodhoz spreadsheet — the seed data; nothing works without it
- Condition status display (four-state: normal / inspection required / repair required / critical) — decision-support at a glance
- Trilingual UI (RU/KK/EN) — non-negotiable from day one
- Search and filter structures — basic navigability with multilingual FTS
- Provenance tracking on initial data — trust infrastructure built into the data model from the start (elevated from P2 to P1)
- Portfolio dashboard — condition distribution, repair queue, executive view

**Should have (competitive — P2 v1.x):**
- Inspection history timeline — the temporal backbone; enables risk-informed intervals
- Document attachment per structure — scanned passports, inspection reports, EAPs
- Risk-informed inspection interval assessment — semi-quantitative, defensible, aligns with World Bank/FEMA/FERC practice
- Repair need determination with red-flag overrides — blended score with explicit critical triggers (seepage, deformation, rapid erosion)
- OGC API Features/Tiles compliance — the integration deliverable for government systems
- Human-in-the-loop review workflow — accept/link/reject with evidence display
- Role-based access control (full) — administrator, engineer, inspector, viewer

**Defer (v2+ differentiators — P3):**
- Evidence-fusion candidate discovery (OSM + satellite + documents) — finds "unknown unknowns"; complex, requires STAC + TiTiler + LangGraph
- STAC catalog for EO evidence — satellite imagery metadata; pairs with discovery
- Four-state matching taxonomy + multilingual matching — depends on discovery producing candidates
- AI copilot with evidence-grounded Q&A — highest complexity; requires provenance + pgvector + LangGraph; IBM research shows grounding reduces overclaims from 28% to 2%
- Offline PWA field mode — highest engineering complexity; offline capture, deferred sync, conflict resolution
- Confidence scoring on AI-inferred attributes — depends on AI features existing

**Explicitly out of scope (anti-features):**
- Real-time IoT sensor integration, full InSAR processing, native mobile apps, autonomous AI condition assignment, public Nominatim geocoding, real-time alerting/EAP management, complex hydraulic modeling, other oblasts beyond Zhambyl

### Architecture Approach

The architecture follows the eoAPI reference pattern: a shared PostgreSQL/PostGIS database with TiPG and TiTiler as separate FastAPI-based services reading from it, plus a custom FastAPI for business logic. This gives a dual API surface — TiPG for standards-compliant read-only OGC access (QGIS, ArcGIS, government integration) and FastAPI for read-write business logic (auth, search, AI copilot, ingestion). TiPG auto-discovers PostGIS tables with geometry columns, meaning the data model design directly determines the API surface. PostGIS is the single system of record; pgvector lives alongside relational data enabling hybrid search in one SQL query. LangGraph orchestrates human-in-the-loop workflows with PostgreSQL checkpointing for state persistence across restarts. See [ARCHITECTURE.md](./ARCHITECTURE.md) for component boundaries, data flow diagrams, code patterns, and scalability analysis.

**Major components:**
1. **Next.js PWA** — UI rendering, MapLibre map display, offline capture (Dexie/IndexedDB), trilingual i18n
2. **FastAPI Main API** — Auth, business logic, search, AI copilot endpoints, CRUD operations
3. **TiPG** — OGC API Features + Tiles from PostGIS (read-only, standards-compliant, auto-discovered)
4. **TiTiler** — Dynamic raster tile serving from COGs/STAC items in MinIO
5. **PostgreSQL + PostGIS + pgvector** — System of record for all structure data, spatial indexes, vector embeddings, provenance
6. **MinIO** — S3-compatible object storage for COGs, documents, photos, voice notes
7. **Redis** — Response cache, Celery message broker, session store, rate limiting
8. **Celery Worker** — Background processing: OCR, data ingestion, tile pre-generation, LangGraph workflow execution

**Key patterns to follow:**
- PostGIS as system of record with JSONB provenance on every record
- Hybrid search in single SQL query (tsvector + pgvector with RRF-style fusion)
- LangGraph human-in-the-loop with PostgreSQL checkpointing (never MemorySaver in production)
- OGC API as integration boundary (TiPG for external GIS clients, FastAPI for custom logic)
- Pre-projected geometry columns for tile generation (avoid runtime ST_Transform)

**Key anti-patterns to avoid:**
- Dual system of record (PostGIS + Milvus) — use pgvector instead
- Pre-generating all tiles — use dynamic ST_AsMVT with Redis cache
- LLM as decision maker — always human-in-the-loop for safety-critical assignments
- Monolithic FastAPI with embedded TiPG/TiTiler — keep services separate for independent scaling

### Critical Pitfalls

Twenty-two domain-specific pitfalls documented across all technology layers, verified against official docs, EPSG registry, GitHub issues, and production post-mortems. See [PITFALLS.md](./PITFALLS.md) for full details, prevention strategies, warning signs, and recovery costs.

1. **Kazakhstan coordinate system transition (QazTRF-23 vs Pulkovo 1942)** — #1 critical pitfall. QazTRF-23 (EPSG:10941) replaced Pulkovo 1942 on 2025-01-01. The NTv2 grid file (`qazgrid_kz.gsb`) is not bundled with PROJ. Getting this wrong places structures 50-200m off. **Prevention:** Standardize on EPSG:4326 storage, install grid file, pin PROJ >= 9.4, transform via QazTRF-23 intermediate (0.1m accuracy vs 2-5m direct). Must be solved in the Data Ingestion phase before any map display.

2. **PostGIS geometry/geography type mixing** — Runtime casts between geometry and geography bypass GiST indexes entirely, triggering sequential scans. A 10ms query becomes 2+ seconds. **Prevention:** Store `geometry(POINT, 4326)` with explicit SRID; add separate `geography` column with GiST index if meter-based queries needed; use `ST_DWithin` for filtering, never `ST_Distance` in WHERE; run `EXPLAIN ANALYZE` on every spatial query.

3. **PWA offline sync data loss (last-write-wins without conflict resolution)** — Highest-risk for field operations. Field inspectors' detailed updates silently overwritten by document-level LWW. **Prevention:** Design conflict resolution model BEFORE any offline code. Use field-level merge, Hybrid Logical Clocks, revision tracking, UUIDs for record IDs, outbox pattern. Never auto-resolve inspection records — queue for human review.

4. **Kazakh Cyrillic Extended font rendering** — 9 characters beyond basic Russian Cyrillic need `cyrillic-ext` font subset (U+0460-U+052F). Without it, Kazakh text shows mixed typefaces. **Prevention:** Always load `latin`, `cyrillic`, and `cyrillic-ext` subsets. Test with actual Kazakh text. Must be addressed in Frontend Foundation phase.

5. **TiPG OGC API compliance gaps** — TiPG does not implement Features Part 2 (CRS by Reference) and fails official CITE tests due to FastAPI OpenAPI content-type issues. **Prevention:** Don't claim full compliance — claim specific parts implemented (Common 1+2, Features 1+3, Tiles 1). Run CITE tests early, document known failures, be transparent with integration partners.

**Additional notable pitfalls:** Vector tile bloat from `SELECT *` in ST_AsMVT (Pitfall 3), MinIO presigned URL signature mismatch behind reverse proxy (Pitfall 5), LangGraph state management failures without reducers/checkpointing (Pitfall 6), Docker Compose dependency ordering (Pitfall 8), Milvus over-provisioning for small datasets (Pitfall 9 — reinforces pgvector recommendation), OCR quality on Russian scanned documents (Pitfall 10), multilingual FTS without Russian language configuration (Pitfall 12), COG generation without web-optimized alignment (Pitfall 13), MapLibre feature state performance degradation (Pitfall 14), service worker caching API responses too aggressively (Pitfall 15).

## Implications for Roadmap

Based on combined research across all four dimensions, the following 7-phase structure is recommended. Phases 1-3 deliver the MVP (P1 features), Phase 4 delivers v1.x expansion (P2 features), and Phases 5-7 deliver v2+ differentiators (P3 features). Phases 6 and 7 can be developed in parallel as they are independent.

### Phase 1: Foundation & Infrastructure

**Rationale:** Everything depends on the data model and infrastructure. Provenance tracking must be built into the schema from the start (elevated from P2 to P1 by features research). Docker Compose healthchecks must be correct before any reliable development. Trilingual i18n and Kazakh font rendering must be established before any UI work.

**Delivers:** Docker Compose stack (PostgreSQL/PostGIS/pgvector, Redis, MinIO, FastAPI, Celery); database schema with structures, inspections, provenance, evidence_sources tables; FastAPI + Alembic scaffold; Next.js + next-intl trilingual setup with cyrillic-ext fonts; MinIO configured with MINIO_SERVER_URL.

**Addresses features:** Provenance tracking (initial), trilingual UI foundation, RBAC foundation.

**Avoids pitfalls:** #8 (Docker Compose startup races — healthchecks + service_healthy), #5 (MinIO presigned URL signatures — MINIO_SERVER_URL), #4 (Kazakh font rendering — cyrillic-ext subset), #2 (geometry/geography schema pattern established before any spatial queries).

**Uses stack:** PostgreSQL 17 + PostGIS 3.5 + pgvector, Redis 7, MinIO, FastAPI, Alembic, Next.js 16, next-intl, Tailwind CSS 4.

### Phase 2: Data Ingestion & Spatial API

**Rationale:** The map needs data to display. The Kazvodhoz spreadsheet is the critical-path seed data. Coordinate transformation (QazTRF-23) must be solved here — it is the #1 pitfall and blocks all map display. The spatial API (TiPG + FastAPI CRUD) can be built in parallel with the ingestion pipeline since they are separate codebases. This phase establishes the OGC API surface that TiPG auto-discovers from the PostGIS schema.

**Delivers:** Kazvodhoz spreadsheet ingestion pipeline with coordinate transformation and provenance; TiPG OGC API Features/Tiles endpoints; FastAPI CRUD endpoints for structures; multilingual full-text search (PostgreSQL russian config + pg_trgm + Kazakh normalization); structure inventory in PostGIS.

**Addresses features:** Data ingestion from Kazvodhoz, structure inventory/registry, search and filter, OGC API Features/Tiles compliance (initial).

**Avoids pitfalls:** #1 (QazTRF-23 coordinate transition — grid file, PROJ >= 9.4, transform chain), #11 (TiPG compliance gaps — document conformance classes), #12 (multilingual FTS — russian config + per-record language), #22 (Kazakh character normalization — transliteration layer), #17 (OSM attribution — set up attribution control).

**Uses stack:** TiPG 1.3, FastAPI, SQLAlchemy 2 + GeoAlchemy2, asyncpg, Celery (for ingestion jobs), pg_trgm.

### Phase 3: Map UI & Digital Passport

**Rationale:** The map is the primary interface — this is what stakeholders see first. The digital passport is the canonical record that everything else builds on. The portfolio dashboard gives decision-makers the executive view. These are the remaining P1 MVP features. With data ingested and APIs standing, the frontend can now render the full MVP experience.

**Delivers:** MapLibre interactive map with structure status visualization (four-state color coding via tile properties, not feature state); digital passport detail view (identity, type, geometry, specs, current status, provenance); condition status display (four-state model); portfolio dashboard (condition distribution, repair queue, geographic distribution); trilingual UI fully functional.

**Addresses features:** Interactive map with status visualization, digital passport per structure, condition status display (four-state), portfolio dashboard, trilingual UI (complete).

**Avoids pitfalls:** #3 (vector tile bloat — explicit property selection, pre-projected geometry), #14 (MapLibre feature state — data-driven styling via tile properties), #18 (stale vector tiles — cache invalidation on data update), #19 (MapLibre style URL — self-hosted style JSON).

**Uses stack:** MapLibre GL JS 5, TanStack Query, Zustand, TiPG (vector tiles), FastAPI (passport data).

### Phase 4: Inspection Lifecycle & Risk Models

**Rationale:** Once the MVP (map + passport + condition) is validated by stakeholders, the next layer is the temporal backbone: inspection history, document attachment, and the analytical models that operate on inspection data. Risk-informed inspection intervals and repair determination with red-flag overrides are the decision-support features that justify the system's existence to engineers. These are all P2 features that depend on the core registry being stable.

**Delivers:** Inspection history timeline per structure; document attachment (MinIO presigned URLs for upload/download); risk-informed inspection interval assessment (semi-quantitative, World Bank/FEMA-aligned); repair need determination with red-flag overrides; full RBAC (administrator, engineer, inspector, viewer); export/reporting (CSV, GeoJSON, PDF).

**Addresses features:** Inspection history timeline, document attachment, risk-informed inspection intervals, repair need with red-flag overrides, RBAC (full), export/reporting.

**Avoids pitfalls:** #2 (geometry/geography in spatial queries — already established pattern), #20 (Celery task idempotency — acks_late + idempotency keys for ingestion retry).

**Uses stack:** FastAPI, MinIO (presigned URLs), Celery, Pydantic (risk model), LangGraph (not yet — risk model is deterministic, not workflow-based).

### Phase 5: Evidence-Fusion Discovery & Matching

**Rationale:** This is where the product differentiates from all competitors. No commercial dam safety platform combines OSM tags, hydrography, satellite water indices, and document mentions to discover structures missing from registries. This phase requires the STAC/COG infrastructure (TiTiler + MinIO), the LangGraph workflow for evidence fusion, the OCR pipeline for scanned passports, and the four-state matching taxonomy with multilingual matching. It depends on the core registry being stable (Phases 1-4) because discovery compares candidates against existing records.

**Delivers:** STAC catalog for EO evidence; TiTiler raster serving from COGs; OSM data integration; satellite water index computation (NDWI/MNDWI from Sentinel-2); evidence-fusion locator algorithm (LangGraph workflow); OCR pipeline for scanned passports (Tesseract with preprocessing); four-state matching taxonomy (matched / likely-match / new-candidate / conflict); multilingual matching (transliteration + dictionaries + pg_trgm); human-in-the-loop review workflow (LangGraph interrupt + checkpointing); confidence scoring on AI-inferred attributes.

**Addresses features:** Evidence-fusion candidate discovery, STAC catalog, four-state matching taxonomy, multilingual matching, human-in-the-loop review workflow, confidence scoring, OCR document processing.

**Avoids pitfalls:** #10 (OCR quality — preprocessing, tessdata_best, confidence scoring, human review for low-confidence), #13 (COG web-optimized — `rio cogeo create --web-optimized`), #6 (LangGraph state management — explicit reducers, PostgresSaver, consistent thread_id), #16 (LangGraph checkpoint store — PostgresSaver in production, never MemorySaver), #17 (OSM attribution — display on map, store in provenance).

**Uses stack:** TiTiler, MinIO (COGs), LangGraph 1.0, Celery (OCR jobs), pgvector (semantic search for matching), Tesseract/PaddleOCR, rio-cogeo, STAC.

### Phase 6: PWA Field Mode

**Rationale:** Offline field inspection is the highest engineering complexity feature and the highest risk for data loss. It must be built after the office-based workflow is validated (Phases 1-4) and after the core entities (passport, inspections) exist. The conflict resolution model must be designed before any offline capture code is written — this is the core engineering challenge. This phase can be developed in parallel with Phase 7 (AI Copilot) as they are independent.

**Delivers:** Serwist service worker with correct caching strategies (NetworkFirst for API, CacheFirst for assets); offline IndexedDB capture (Dexie) for photos, voice notes, coordinates, condition assessments; deferred sync with field-level merge conflict resolution; Hybrid Logical Clocks for clock skew resilience; conflict notification UI; GPS coordinate correction; voice note transcription (post-sync); PWA installability.

**Addresses features:** Offline PWA field mode, deferred sync, photo/voice capture, coordinate correction, conflict resolution.

**Avoids pitfalls:** #7 (offline sync data loss — field-level merge, HLCs, revision tracking, UUIDs, outbox pattern, human review for inspection conflicts), #15 (service worker caching — NetworkFirst for API, CacheFirst for static, never cache mutations), #21 (i18n middleware redirect loops — correct matcher pattern).

**Uses stack:** Serwist, Dexie.js, TanStack Query (sync queue), MediaRecorder API, Geolocation API, FastAPI (sync endpoints).

### Phase 7: AI Copilot

**Rationale:** The AI copilot is the capstone feature — it depends on all prior data being clean, canonical, and provenance-tracked. Its value is evidence-grounded answers with source citations, which requires provenance (Phase 1-2), the full registry (Phase 2-3), inspection history (Phase 4), and potentially discovery evidence (Phase 5). IBM research shows that grounding reduces expert-rated overclaims from 28% to 2%, validating the evidence-grounded approach. This phase can be developed in parallel with Phase 6 (PWA Field Mode) as they are independent.

**Delivers:** LangGraph RAG workflow for evidence-grounded Q&A; pgvector hybrid search (tsvector + vector similarity in one SQL query); source citations on every answer (inspection records, registry rows, OSM ways, document references); confidence levels on responses; streaming responses to frontend; trilingual query support (RU/KK/EN).

**Addresses features:** AI copilot with evidence-grounded Q&A, hybrid search, source citations, confidence levels.

**Avoids pitfalls:** #9 (Milvus over-provisioning — use pgvector, no extra containers), #6 (LangGraph state management — reducers, PostgresSaver), #16 (LangGraph checkpoint store — PostgresSaver in production).

**Uses stack:** LangGraph 1.0, pgvector (hybrid search), LangChain (document loaders, embeddings, LLM wrappers), FastAPI (copilot endpoints), PostgreSQL (checkpoint store).

### Phase Ordering Rationale

- **Foundation first (Phase 1):** Everything depends on the data model. Provenance must be built into the schema from the start — it is the trust infrastructure that the AI copilot, matching taxonomy, and confidence scoring all depend on. Infrastructure pitfalls (Docker healthchecks, MinIO configuration, font rendering) must be solved before any feature work.
- **Data ingestion + spatial API second (Phase 2):** The map needs data to display. Coordinate transformation (QazTRF-23) is the #1 critical pitfall and blocks all map display. The ingestion pipeline and spatial API can be developed as parallel tracks (backend vs. geo-infrastructure).
- **Map + passport third (Phase 3):** This completes the MVP — the "Kazvodhoz spreadsheet, made credible and visible." Stakeholders validate the core thesis before investing in advanced features.
- **Inspection lifecycle fourth (Phase 4):** The temporal backbone. Risk models need inspection history to compute intervals. This is the v1.x expansion that makes the system useful for engineering decisions.
- **Discovery fifth (Phase 5):** The differentiator. Depends on stable core registry to compare candidates against. Most complex single phase (STAC + TiTiler + LangGraph + OCR + matching).
- **PWA + AI copilot last (Phases 6-7, parallel):** Both are v2+ features that depend on all prior data. They are independent of each other and can be developed in parallel. PWA is highest engineering risk (offline sync); AI copilot is highest complexity (RAG + provenance + multilingual).

### Research Flags

Phases likely needing deeper research during planning (`/gsd-plan-phase --research-phase`):

- **Phase 2 (Data Ingestion & Spatial API):** QazTRF-23 coordinate transformation is niche and critical — grid file availability, PROJ version compatibility, and transformation chain need validation with actual Kazvodhoz data. Multilingual FTS configuration for Kazakh (no native PostgreSQL stemmer) needs testing.
- **Phase 5 (Evidence-Fusion Discovery & Matching):** Evidence-fusion algorithm combining OSM tags, hydrography, satellite water indices, and document mentions is non-trivial — no commercial product ships this. STAC/COG pipeline specifics (imagery sources, water index computation, COG generation workflow) need detailed design. OCR preprocessing for Russian/Kazakh scanned documents needs testing with actual government scans.
- **Phase 6 (PWA Field Mode):** Offline sync conflict resolution is the highest-risk area — field-level merge model, Hybrid Logical Clocks implementation, outbox pattern, and conflict notification UX all need design before implementation.
- **Phase 7 (AI Copilot):** RAG chunking strategy for Russian/Kazakh Cyrillic documents needs research — standard English-centric chunking may not work well. LangGraph state schema design (reducers, thread_id management) needs careful planning to avoid the state management failures documented in Pitfall 6.

Phases with standard patterns (skip research-phase):

- **Phase 1 (Foundation & Infrastructure):** Docker Compose, FastAPI scaffold, Alembic migrations, Next.js setup — well-documented, established patterns. Pitfalls are known and prevention strategies are concrete.
- **Phase 3 (Map UI & Digital Passport):** MapLibre + TiPG vector tiles, React component patterns, dashboard charts — well-documented. Key pitfall (feature state performance) has a clear prevention (data-driven styling via tile properties).
- **Phase 4 (Inspection Lifecycle & Risk Models):** CRUD operations, document upload, semi-quantitative risk scoring — standard patterns. Risk model is deterministic (not ML), reducing complexity.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All major versions verified via Context7 + official docs + PyPI. Real-world precedent (GeoLens, eoAPI, geostack) confirms the pattern. Three adjustments (pgvector, Serwist, Celery) independently validated by stack and pitfalls research. |
| Features | HIGH | Extensive survey of 15+ competitors and academic projects. Feature landscape well-mapped with clear table stakes, differentiators, and anti-features. Dependency graph validated against architecture research. Risk frameworks (World Bank, FEMA/FERC) provide strong backing for inspection interval model. AI grounding research (IBM IndustryAssetEQA) provides empirical evidence for evidence-grounded approach. |
| Architecture | HIGH | Standard geospatial micro-service pattern validated by eoAPI and GeoLens reference architectures. Component boundaries clear. Data flow diagrams cover all major scenarios. Scalability analysis shows the architecture handles 1,400 structures trivially with headroom to 50K+. TiPG auto-discovery pattern well-understood. |
| Pitfalls | HIGH | 22 pitfalls verified against official docs, EPSG registry, GitHub issues, and production post-mortems. Critical pitfalls (QazTRF-23, PostGIS index bypass, PWA sync, LangGraph state) have concrete prevention strategies and phase assignments. Recovery costs documented. "Looks done but isn't" checklist provides verification gates. |

**Overall confidence:** HIGH

### Gaps to Address

- **QazTRF-23 grid file availability:** The `qazgrid_kz.gsb` NTv2 grid file must be sourced and verified in the PROJ data directory. Some EPSG registries return `null` for the proj4 string of EPSG:10941. Need to validate the full transformation chain (Pulkovo 1942 → QazTRF-23 → WGS 84) with actual Kazvodhoz coordinates during Phase 2 planning.
- **Kazakh OCR quality:** Tesseract's `rus.traineddata` may confuse Kazakh-specific characters. PaddleOCR is a potential alternative. Must test with actual scanned Kazvodhoz passports (government scan quality varies wildly) during Phase 5 planning.
- **Trilingual fuzzy matching:** pg_trgm works for Latin and Cyrillic but Kazakh-specific characters (ә, ғ, қ, ң, ө, ұ, ү, h, і) need a normalization/transliteration layer. Must test with real Kazvodhoz data (Russian names) against OSM data (English/transliterated names) during Phase 5 planning.
- **TiPG OGC CITE compliance:** Known CITE test failures (issue #84, WontFix) and missing Features Part 2 (CRS by Reference). Must run CITE tests early in Phase 2 and document pass/fail per conformance class for integration partners.
- **PWA sync conflict resolution model:** Field-level merge vs document-level LWW, Hybrid Logical Clocks implementation, and conflict notification UX all need design before any offline code is written. This is the core engineering challenge of Phase 6.
- **RAG chunking for Cyrillic text:** Standard English-centric chunking (sentence boundary, token count) may not work well for Russian/Kazakh documents with different punctuation and morphology. Needs experimentation during Phase 7 planning.
- **Kazakh Latin script transition:** Kazakhstan is transitioning Kazakh to a Latin script (target 2031). The i18n system should store a `script` field alongside `language` to accommodate both Cyrillic and Latin Kazakh in the future. Not a blocker for v1 but should be designed for.

## Sources

### Primary (HIGH confidence)

- **Context7 libraries:** `/vercel/next.js` (v16.2.9), `/fastapi/fastapi` (v0.128.0), `/maplibre/maplibre-gl-js` (v5.19.0), `/developmentseed/titiler`, `/websites/langchain_oss_python_langgraph`, `/websites/milvus_io` — version verification and API patterns
- **EPSG Registry:** QazTRF-23 (EPSG:10941), Pulkovo 1942 (EPSG:4284), transformation EPSG:10964 with qazgrid_kz.gsb — https://epsg.org/crs_10941/QazTRF-23.html
- **PostGIS official docs:** Performance tips, ST_AsMVT behavior — https://postgis.net/docs/performance_tips.html
- **PostGIS release notes:** v3.5.7 (June 2026) — https://postgis.net/docs/manual-3.5/en/release_notes.html
- **TiPG official docs + PyPI:** v1.3.1 (Feb 2026), OGC API Features/Tiles — https://developmentseed.org/tipg/
- **TiPG GitHub issues:** #84 (CITE test failures, WontFix), OGC Features Part 2 not implemented — https://github.com/developmentseed/tipg
- **Martin GitHub:** #2365 (no OGC API Features support, no plans) — https://github.com/maplibre/martin
- **MapLibre GitHub:** #6633 (feature state performance), #7590 (fix, May 2026) — https://github.com/maplibre/maplibre-gl-js
- **Tesseract docs:** ImproveQuality guide, Data Files (tessdata_best vs fast) — https://github.com/tesseract-ocr/tessdoc
- **Docker Compose docs:** Startup order, healthcheck patterns — https://docs.docker.com/compose/how-tos/startup-order/
- **rio-cogeo docs:** Advanced topics, web-optimized flag — https://cogeotiff.github.io/rio-cogeo/Advanced/
- **PostgreSQL docs:** pg_trgm extension — https://www.postgresql.org/docs/current/pgtrgm.html
- **Next.js docs:** Internationalization guide — https://nextjs.org/docs/app/guides/internationalization
- **Serwist docs:** Configuration, Next.js integration — https://serwist.pages.dev/docs/next/config
- **next-intl:** v4.13.0 (May 2026) — https://github.com/amannn/next-intl
- **GeoAlchemy2:** v0.18.4 — https://geoalchemy-2.readthedocs.io/
- **World Bank:** Technical Note on Portfolio Risk Assessment Using Risk Index — documents1.worldbank.org
- **FEMA:** Federal Guidelines for Dam Safety Risk Management (P1025) — damssafety.org
- **FERC:** RIDM Guidelines Chapter 3, Engineering Guidelines Chapter 18 (SQRA) — ferc.gov, hydro.org
- **USBR:** Best Practices Chapter A-4 (Semi-Quantitative Risk Analysis) — usbr.gov
- **IBM IndustryAssetEQA:** Neurosymbolic EQA for industrial assets (ACL 2026) — aclanthology.org (grounding reduces overclaims 28% → 2%)
- **OGC Standards:** API Features, API Tiles, STAC Community Standard 25-004 v1.1.0 — ogc.org
- **Kazhydromet:** Interactive hydrological monitoring map (377 stations) — kazhydromet.kz
- **kazdams.kz:** GIS for dam monitoring in Kazakhstan (IRN AP19675038) — jstage.jst.go.jp

### Secondary (MEDIUM confidence)

- **GeoLens reference architecture:** PostGIS + pgvector + MapLibre + TiTiler + FastAPI — https://getgeolens.com/
- **eoAPI reference architecture:** Development Seed's TiPG + TiTiler + STAC pattern
- **pgvector vs Milvus comparisons:** Multiple sources (March-June 2026) — modern-datatools.com, DEV.to, Instaclustr, Zilliz blog
- **Celery vs ARQ:** bytay.dev (May 2026), Medium benchmarks (May 2026), Stackademic (April 2026)
- **PostGIS anti-patterns:** Medium article verified against official docs — philmcc
- **ST_AsMVT performance:** PostGIS core developer blog — blog.cleverelephant.ca
- **PWA sync conflict resolution:** dev.to, sachith.co.uk — offline-first patterns
- **LangGraph troubleshooting:** sumanmichael.github.io, markaicode.com — verified against LangGraph docs
- **MinIO Nginx proxy:** vineethnk.in blog — signature mismatch patterns
- **Kazakh font rendering:** imarch.dev — verified against Unicode block definitions
- **Kazakh alphabet transition:** Wikipedia — en.wikipedia.org/wiki/Kazakh_alphabets
- **PWA offline field collection:** terminalskills.io, CivicPlus, GrowXLabs, InspectSync — production PWA patterns
- **Provenance frameworks:** W3C PROV, GeoPROV (Semantic Web Journal 2025), World Historical Gazetteer attestation model
- **Satellite infrastructure detection:** GeoAI4Water (HeiGIT), IGraSS (IJCAI 2025) — water infrastructure mapping approaches

### Tertiary (LOW confidence)

- **MinIO production settings:** markaicode.com — operational configuration (needs validation with specific MinIO version)
- **Multilingual FTS configurations:** kindatechnical.com — Kazakh lacks native PostgreSQL stemmer (needs custom solution validation)
- **next-intl pitfalls:** 32blog.com — middleware redirect patterns (needs testing with Next.js 16)

---
*Research completed: 2026-06-25*
*Ready for roadmap: yes*
