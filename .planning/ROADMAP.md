# Roadmap: Zhambyl Hydraulic Structures Catalog

## Overview

This roadmap builds the digital operating layer for hydraulic structures in Zhambyl Oblast in seven phases. It starts with infrastructure and the core data model (Phase 1), ingests the Kazvodhoz registry and stands up spatial APIs (Phase 2), delivers the map-first MVP with digital passports and portfolio analytics (Phase 3), adds the inspection lifecycle and risk-informed decision models (Phase 4), differentiates with evidence-fusion discovery and human-in-the-loop matching (Phase 5), and finishes with two independent capabilities: offline PWA field inspection (Phase 6) and an evidence-grounded AI copilot powered by the existing adapted RAG agent (Phase 7). Each phase delivers an end-to-end user capability that can be validated before the next begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Infrastructure** - Docker stack, PostGIS schema with provenance, trilingual i18n, MinIO setup
- [ ] **Phase 2: Data Ingestion & Spatial API** - Kazvodhoz ingestion with coordinate transformation, TiPG OGC API, REST CRUD, multilingual search
- [ ] **Phase 3: Map UI & Digital Passport** - Interactive MapLibre map, digital passport view, portfolio dashboard, filtering — the MVP
- [ ] **Phase 4: Inspection Lifecycle & Risk Models** - Inspection history, document attachment, risk-informed intervals, repair status, RBAC, exports
- [ ] **Phase 5: Evidence-Fusion Discovery & Matching** - OSM/satellite/OCR evidence-fusion locator, four-state matching, human-in-the-loop review, STAC catalog
- [ ] **Phase 6: PWA Field Mode** - Offline capture, deferred sync with field-level conflict resolution, voice transcription, sync status UI
- [ ] **Phase 7: AI Copilot** - Evidence-grounded Q&A with source citations, hybrid search, trilingual queries — integrating existing RAG agent

## Phase Details

### Phase 1: Foundation & Infrastructure
**Goal**: The project has a running development environment with the core data model, trilingual i18n, and infrastructure ready for feature development
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: DATA-07, UI-01, UI-02, INT-04
**Success Criteria** (what must be TRUE):
  1. Developer can start all services (PostgreSQL/PostGIS/pgvector, Redis, MinIO, FastAPI, Celery) with a single Docker Compose command and they report healthy
  2. User can switch the UI between Russian, Kazakh, and English and see all interface text translated correctly, with Kazakh-specific Cyrillic characters (ә, ғ, қ, ң, ө, ұ, ү, h, і) rendering in the correct typeface
  3. Database schema includes provenance tracking on all structure records, and a developer can query the source, confidence, and timestamp of any stored fact
  4. MinIO object storage is configured and serves presigned URLs correctly, with the architecture separation established: imagery evidence in STAC/COG/MinIO, structure features in PostGIS
**Plans**: TBD
**UI hint**: yes

### Phase 2: Data Ingestion & Spatial API
**Goal**: The Kazvodhoz canal registry is ingested into PostGIS with correct coordinates, searchable via multilingual full-text search, and accessible via OGC API and REST endpoints
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-08, INT-01, INT-03
**Success Criteria** (what must be TRUE):
  1. All 444 Kazvodhoz canal records are loaded into PostGIS with correctly transformed coordinates — structures appear at expected geographic positions, not 50-200m offset from QazTRF-23 transformation errors
  2. External GIS client (e.g., QGIS) can connect to the OGC API Features/Tiles endpoint via TiPG and load hydraulic structure features with spatial and attribute filtering
  3. User can search and filter structures by name, type, condition, district, or location using multilingual queries (Russian, Kazakh, English) with fuzzy matching that handles transliteration differences
  4. Frontend can call REST API endpoints to list, retrieve, and search structures, with CRUD endpoints operational for the application
**Plans**: TBD

### Phase 3: Map UI & Digital Passport
**Goal**: Users can explore all hydraulic structures on an interactive map, view each structure's digital passport, and see portfolio-wide analytics — completing the MVP
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: MAP-01, MAP-02, MAP-03, MAP-04, MAP-05, DATA-04
**Success Criteria** (what must be TRUE):
  1. User can view an interactive map showing all hydraulic structures, hydrological stations, and related facilities in Zhambyl Oblast with color-coded status symbology (normal / inspection required / repair required / critical)
  2. User can click any structure on the map to open its digital passport showing identity, type, geometry, administrative location, technical specifications, current status, and source provenance
  3. Decision-maker can view a portfolio dashboard showing condition distribution, repair queue, inspection coverage, and geographic distribution heatmap
  4. User can filter both the map and dashboard by district, basin, structure type, condition, and inspection status, with filters applying consistently across both views
**Plans**: TBD
**UI hint**: yes

### Phase 4: Inspection Lifecycle & Risk Models
**Goal**: Engineers can track inspection history, attach documents, and rely on risk-informed inspection intervals and repair priorities with appropriate role-based access
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: DATA-05, DATA-06, RISK-01, RISK-02, RISK-03, RISK-04, RISK-05, RISK-06, RISK-07, RISK-08
**Success Criteria** (what must be TRUE):
  1. User can view an inspection history timeline per structure showing date, inspector, findings, photos, and condition at time of inspection
  2. User can attach and download documents (scanned passports, inspection reports, photos) to structure records
  3. System displays a risk-informed inspection interval for each structure as a legible urgency level (30 days through 24 months, with emergency override) computed from a semi-quantitative model (condition, consequence, seasonality, data staleness)
  4. System assigns one of four repair statuses (normal / inspection required / repair required / critical) using a blended condition score with red-flag overrides for critical indicators, preferring "inspection required" when evidence is weak, stale, or conflicting
  5. Users have role-appropriate access (administrator, engineer, inspector, viewer), engineers can override system recommendations with logged provenance, and users can export structure lists as CSV/GeoJSON and generate inspection reports as PDF in all three languages
**Plans**: TBD
**UI hint**: yes

### Phase 5: Evidence-Fusion Discovery & Matching
**Goal**: The system discovers candidate hydraulic structures from open sources and satellite imagery, compares them against the existing registry, and enables human-in-the-loop verification with confidence tracking
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: DATA-02, DATA-03, DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, DISC-06, INT-02, UI-03
**Success Criteria** (what must be TRUE):
  1. System can locate candidate hydraulic structures by fusing evidence from OSM tags, hydrography, satellite water indices (NDWI/MNDWI from Sentinel-2), and document/OCR mentions from scanned passports
  2. System compares each candidate against the existing database using hierarchical multilingual matching and assigns one of four states: matched, likely-match-needs-review, new-candidate, or conflict
  3. Reviewer can review candidates in a side-by-side workflow showing existing record vs candidate with evidence chips (name similarity, distance, type agreement, source evidence), and accept (add to registry), link (merge with existing), or reject (mark as false positive) each one
  4. User can see confidence badges (HIGH/MEDIUM/LOW) and provenance source chips on all AI-inferred and externally-sourced attributes throughout the UI
  5. STAC catalog is maintained for Earth observation evidence (Sentinel-2 scenes, water index composites) with TiTiler dynamic raster serving from COGs stored in MinIO
**Plans**: TBD
**UI hint**: yes

### Phase 6: PWA Field Mode
**Goal**: Inspectors can install the PWA on any device, capture field data offline, and sync it reliably when connectivity returns without silent data loss
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: FIELD-01, FIELD-02, FIELD-03, FIELD-04, FIELD-05
**Success Criteria** (what must be TRUE):
  1. Inspector can install the PWA on desktop or mobile and use it offline in the field without any network connectivity
  2. Inspector can capture photos, dictate voice notes (Kazakh or Russian), pin corrected GPS coordinates, and fill inspection forms while offline
  3. System syncs field captures when connectivity returns using field-level merge conflict resolution (not last-write-wins), with voice notes transcribed to text post-sync using Kazakh and Russian speech-to-text
  4. Inspector can see per-record sync status (pending / syncing / confirmed / failed) and resolve conflicts through a review UI
**Plans**: TBD
**UI hint**: yes

### Phase 7: AI Copilot
**Goal**: Users can ask natural-language questions about structures and receive evidence-grounded answers with source citations, powered by the existing adapted RAG agent integrated into the platform
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: AI-01, AI-02, AI-03, AI-04, AI-05
**Success Criteria** (what must be TRUE):
  1. User can ask natural-language questions about structures ("Why is this structure marked repair required?", "Show similar incidents in this basin", "Summarize all inspections since 2022") and receive synthesized answers
  2. Every AI copilot answer includes explicit source citations (inspection records, registry rows, OSM ways, document references) that the user can click to verify
  3. AI copilot uses hybrid search combining PostgreSQL full-text + pg_trgm (structured data) + vector semantic similarity (unstructured data) in a single query, integrated from the existing RAG agent at apps/agent/
  4. AI copilot supports trilingual queries (Russian, Kazakh, English) and never makes final engineering decisions — it retrieves and synthesizes evidence for human confirmation
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7
Phases 6 and 7 are independent of each other (both depend on Phase 4) and can be developed in parallel.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Infrastructure | 0/TBD | Not started | - |
| 2. Data Ingestion & Spatial API | 0/TBD | Not started | - |
| 3. Map UI & Digital Passport | 0/TBD | Not started | - |
| 4. Inspection Lifecycle & Risk Models | 0/TBD | Not started | - |
| 5. Evidence-Fusion Discovery & Matching | 0/TBD | Not started | - |
| 6. PWA Field Mode | 0/TBD | Not started | - |
| 7. AI Copilot | 0/TBD | Not started | - |
