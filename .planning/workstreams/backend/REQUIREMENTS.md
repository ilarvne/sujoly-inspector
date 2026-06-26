# Requirements: SuJoly Inspector — Backend

**Defined:** 2026-06-25
**Workstream:** backend
**Core Value:** Every hydraulic structure in Zhambyl has one canonical, evidence-backed record in PostGIS with its current condition, inspection urgency, and repair status — accessible via REST and OGC APIs.

## v1 Requirements

### Data & Storage

- [ ] **DATA-01**: System can ingest the Kazvodhoz canal registry spreadsheet (444 records, 22 columns, Russian) into PostGIS with coordinate transformation (QazTRF-23 / EPSG:10941)
- [ ] **DATA-02**: System can ingest data from OpenStreetMap (water/hydraulic features via Overpass API) with provenance tracking
- [ ] **DATA-03**: System can ingest scanned passport documents via OCR (Russian/Kazakh) with confidence scoring
- [ ] **DATA-05**: System stores inspection history per structure (date, inspector, findings, photo URLs, condition at time of inspection)
- [ ] **DATA-06**: System provides document attachment endpoints (scanned passports, inspection reports, photos) via MinIO presigned URLs
- [x] **DATA-07**: Every fact and status on every structure has a provenance record (source type, source reference, confidence level, timestamp, contributor)
- [ ] **DATA-08**: System provides search and filter endpoints by name, type, condition, district, or location using multilingual full-text search (Russian, Kazakh, English) and fuzzy matching (pg_trgm)

### Discovery & Matching

- [ ] **DISC-01**: System can locate candidate hydraulic structures using evidence-fusion from multiple sources: OSM tags (waterway=canal/dam/weir), hydrography (HydroRIVERS), satellite water indices (NDWI/MNDWI from Sentinel-2), and document/OCR mentions
- [ ] **DISC-02**: System can compare found objects with the existing database using hierarchical multilingual matching (spatial proximity via ST_DWithin → name similarity via pg_trgm → attribute comparison → confidence scoring)
- [ ] **DISC-03**: System assigns one of four matching states to each comparison: matched, likely-match-needs-review, new-candidate, or conflict
- [ ] **DISC-05**: System provides endpoints for reviewer to accept (add to registry), link (merge with existing), or reject (mark as false positive) each candidate
- [ ] **DISC-06**: System computes confidence levels (HIGH/MEDIUM/LOW) on AI-inferred attributes based on evidence agreement across sources

### Inspection & Risk

- [x] **RISK-01**: System computes a risk-informed inspection interval for each structure using a semi-quantitative model: condition score × consequence factor × seasonal modifier × data staleness modifier
- [x] **RISK-02**: System maps inspection urgency to legible intervals: 30 days, 90 days, 180 days, 12 months, 24 months, with emergency override
- [x] **RISK-03**: System determines repair need using a blended condition score (0-100) with red-flag overrides for critical indicators (seepage, deformation, rapid erosion, repeated emergencies)
- [x] **RISK-04**: System assigns one of four repair statuses: normal, inspection required, repair required, critical condition
- [x] **RISK-05**: System prefers "inspection required" over false certainty when evidence is weak, stale, or conflicting
- [ ] **RISK-06**: System provides endpoints for engineer role to override system-recommended inspection intervals and repair statuses with logged provenance
- [ ] **RISK-07**: System enforces administrator, engineer, inspector, and viewer role permissions (RBAC)
- [ ] **RISK-08**: System provides export endpoints for structure lists as CSV/GeoJSON and inspection report generation as PDF in all three languages

### Integration

- [ ] **INT-01**: System exposes OGC API Features (Part 1 Core, Part 3 Filtering/CQL2) and OGC API Tiles (Part 1 Core) via TiPG for external GIS clients (QGIS, ArcGIS, government systems)
- [ ] **INT-02**: System maintains a STAC catalog for Earth observation evidence (Sentinel-2 scenes, water index composites) with TiTiler dynamic raster serving from COGs
- [ ] **INT-03**: System exposes a REST API for the application frontend (CRUD, search, copilot, ingestion, sync endpoints)
- [x] **INT-04**: System separates imagery evidence (STAC/COG in MinIO) from structure features (PostGIS) per the architecture principle

### AI & Search (Backend)

- [ ] **AI-03**: System provides hybrid search: PostgreSQL full-text + pg_trgm (structured) + pgvector semantic similarity (unstructured) in a single query
- [ ] **AI-04**: System enforces that AI copilot never makes final engineering decisions — it retrieves and synthesizes evidence; humans confirm all condition assignments

## Out of Scope (Backend)

| Feature | Reason |
|---------|--------|
| Frontend UI components | Handled by frontend workstream |
| Map rendering | Handled by frontend workstream (MapLibre) |
| PWA service worker | Handled by frontend workstream |
| OpenUI renderer | Handled by frontend workstream |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-07 | Phase 1 | Complete |
| INT-04 | Phase 1 | Complete |
| DATA-01 | Phase 2 | Pending |
| DATA-08 | Phase 2 | Pending |
| INT-01 | Phase 2 | Pending |
| INT-03 | Phase 2 | Pending |
| RISK-01 | Phase 3 | Complete |
| RISK-02 | Phase 3 | Complete |
| RISK-03 | Phase 3 | Complete |
| RISK-04 | Phase 3 | Complete |
| RISK-05 | Phase 3 | Complete |
| RISK-06 | Phase 3 | Pending |
| RISK-07 | Phase 3 | Pending |
| RISK-08 | Phase 3 | Pending |
| DATA-05 | Phase 3 | Pending |
| DATA-06 | Phase 3 | Pending |
| DATA-02 | Phase 4 | Pending |
| DATA-03 | Phase 4 | Pending |
| DISC-01 | Phase 4 | Pending |
| DISC-02 | Phase 4 | Pending |
| DISC-03 | Phase 4 | Pending |
| DISC-05 | Phase 4 | Pending |
| DISC-06 | Phase 4 | Pending |
| INT-02 | Phase 4 | Pending |
| AI-03 | Phase 5 | Pending |
| AI-04 | Phase 5 | Pending |

**Coverage:** 26 requirements mapped to 5 phases

---
*Requirements defined: 2026-06-25*
*Last updated: 2026-06-25 after workstream split*
