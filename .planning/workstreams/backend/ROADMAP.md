# Roadmap: SuJoly Inspector — Backend

## Overview

Backend workstream: FastAPI + PostgreSQL/PostGIS + TiPG + TiTiler + MinIO + Redis + Celery. Builds the data layer, spatial APIs, risk models, discovery algorithms, and RAG agent integration. 5 phases, each delivering API endpoints and data capabilities that the frontend workstream consumes.

## Phases

- [ ] **Phase 1: Foundation & Infrastructure** - Docker stack, PostGIS schema with provenance, MinIO, Redis, FastAPI skeleton
- [ ] **Phase 2: Data Ingestion & Spatial API** - Kazvodhoz ingestion with QazTRF-23, TiPG OGC API, REST CRUD, multilingual search
- [ ] **Phase 3: Risk Models & Inspection Logic** - Risk score calculation, inspection intervals, repair status, RBAC, export endpoints
- [ ] **Phase 4: Discovery & Matching Backend** - Evidence-fusion locator, four-state matching, STAC catalog, OCR pipeline
- [ ] **Phase 5: RAG Agent Integration** - Connect adapted RAG agent, hybrid search, tool endpoints for copilot

## Phase Details

### Phase 1: Foundation & Infrastructure
**Goal**: Running Docker stack with PostGIS schema, MinIO, Redis, and FastAPI skeleton with provenance tracking
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: DATA-07, INT-04
**Success Criteria** (what must be TRUE):
  1. Developer starts all services (PostgreSQL/PostGIS/pgvector, Redis, MinIO, FastAPI, Celery) with a single Docker Compose command and they report healthy
  2. Database schema includes provenance tracking on all structure records — developer can query source, confidence, and timestamp of any stored fact
  3. MinIO object storage configured and serves presigned URLs correctly
  4. Architecture separation established: imagery evidence in STAC/COG/MinIO, structure features in PostGIS
**Plans**: TBD

### Phase 2: Data Ingestion & Spatial API
**Goal**: Kazvodhoz registry ingested into PostGIS with correct coordinates, searchable, accessible via OGC API and REST
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-08, INT-01, INT-03
**Success Criteria** (what must be TRUE):
  1. All 444 Kazvodhoz canal records loaded into PostGIS with correctly transformed coordinates — no 50-200m offset from QazTRF-23 errors
  2. External GIS client (QGIS) can connect to OGC API Features/Tiles via TiPG and load structures with filtering
  3. REST API endpoints operational for list, retrieve, search structures with multilingual FTS + pg_trgm fuzzy matching
  4. CRUD endpoints operational for the application frontend
**Plans**: TBD

### Phase 3: Risk Models & Inspection Logic
**Goal**: Risk-informed inspection intervals, repair status, inspection history, document attachment, RBAC, and export endpoints all operational
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: DATA-05, DATA-06, RISK-01, RISK-02, RISK-03, RISK-04, RISK-05, RISK-06, RISK-07, RISK-08
**Success Criteria** (what must be TRUE):
  1. System computes risk-informed inspection interval per structure as legible urgency (30d–24mo + emergency override)
  2. System assigns four repair statuses via blended score + red-flag overrides, preferring "inspection required" on weak evidence
  3. Inspection history endpoints operational (create, list, get with photos via MinIO presigned URLs)
  4. Document attachment endpoints operational (upload, download via MinIO presigned URLs)
  5. RBAC enforced (admin, engineer, inspector, viewer), engineer overrides logged with provenance, export endpoints (CSV/GeoJSON/PDF) in all three languages
**Plans**: TBD

### Phase 4: Discovery & Matching Backend
**Goal**: Evidence-fusion candidate discovery, four-state matching, STAC catalog, and OCR pipeline all operational
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: DATA-02, DATA-03, DISC-01, DISC-02, DISC-03, DISC-05, DISC-06, INT-02
**Success Criteria** (what must be TRUE):
  1. System locates candidates by fusing OSM tags + hydrography + satellite water indices + OCR mentions
  2. System compares each candidate against registry → matched / likely-match-needs-review / new-candidate / conflict
  3. Review endpoints operational (accept / link / reject) with confidence scoring (HIGH/MEDIUM/LOW)
  4. STAC catalog maintained for EO evidence with TiTiler dynamic raster serving from COGs
  5. OCR pipeline operational for scanned passports (Russian/Kazakh) with confidence scoring
**Plans**: TBD

### Phase 5: RAG Agent Integration
**Goal**: Adapted RAG agent connected to platform with hybrid search and tool endpoints for the AI copilot
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: AI-03, AI-04
**Success Criteria** (what must be TRUE):
  1. RAG agent at apps/agent/ connected to platform — tool endpoints (search_structures, get_risk_explanation, etc.) return real data from PostGIS
  2. Hybrid search operational: PostgreSQL FTS + pg_trgm + pgvector semantic similarity in a single query
  3. AI copilot enforces no-final-decision rule — retrieves and synthesizes only, humans confirm condition assignments
  4. SSE streaming endpoint operational for frontend copilot UI consumption
**Plans**: TBD

## Progress

**Execution Order:** 1 → 2 → 3 → (4 and 5 can parallelize after Phase 3)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Infrastructure | 0/TBD | Not started | - |
| 2. Data Ingestion & Spatial API | 0/TBD | Not started | - |
| 3. Risk Models & Inspection Logic | 0/TBD | Not started | - |
| 4. Discovery & Matching Backend | 0/TBD | Not started | - |
| 5. RAG Agent Integration | 0/TBD | Not started | - |
