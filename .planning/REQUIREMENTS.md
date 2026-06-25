# Requirements: Zhambyl Hydraulic Structures Catalog

**Defined:** 2026-06-25
**Core Value:** Every hydraulic structure in Zhambyl has one canonical, evidence-backed record visible on an interactive map with its current condition, inspection urgency, and repair status — enabling data-driven maintenance decisions.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Map & Visualization

- [ ] **MAP-01**: User can view an interactive map displaying all hydraulic structures, hydrological stations, and related facilities in Zhambyl Oblast
- [ ] **MAP-02**: User can see structure status visualization on the map via color-coded symbology (four-state condition: normal / inspection required / repair required / critical)
- [ ] **MAP-03**: User can click any structure on the map to open its digital passport
- [ ] **MAP-04**: Decision-maker can view a portfolio dashboard with condition distribution, repair queue, inspection coverage, and geographic distribution heatmap
- [ ] **MAP-05**: User can filter map and dashboard by district, basin, structure type, condition, and inspection status

### Data & Passport

- [ ] **DATA-01**: System can ingest the Kazvodhoz canal registry spreadsheet (444 records, 22 columns, Russian) into PostGIS with coordinate transformation (QazTRF-23 / EPSG:10941)
- [ ] **DATA-02**: System can ingest data from OpenStreetMap (water/hydraulic features via Overpass API) with provenance tracking
- [ ] **DATA-03**: System can ingest scanned passport documents via OCR (Russian/Kazakh) with confidence scoring
- [ ] **DATA-04**: User can view a digital passport per structure showing identity, type, geometry, administrative location, technical specifications, current status, and source provenance
- [ ] **DATA-05**: User can view inspection history timeline per structure (date, inspector, findings, photos, condition at time of inspection)
- [ ] **DATA-06**: User can attach documents (scanned passports, inspection reports, photos) to structure records via MinIO presigned URLs
- [ ] **DATA-07**: Every fact and status on every structure has a provenance record (source type, source reference, confidence level, timestamp, contributor)
- [ ] **DATA-08**: User can search and filter structures by name, type, condition, district, or location using multilingual full-text search (Russian, Kazakh, English) and fuzzy matching (pg_trgm)

### Discovery & Matching

- [ ] **DISC-01**: System can locate candidate hydraulic structures using evidence-fusion from multiple sources: OSM tags (waterway=canal/dam/weir), hydrography (HydroRIVERS), satellite water indices (NDWI/MNDWI from Sentinel-2), and document/OCR mentions
- [ ] **DISC-02**: System can compare found objects with the existing database using hierarchical multilingual matching (spatial proximity via ST_DWithin → name similarity via pg_trgm → attribute comparison → confidence scoring)
- [ ] **DISC-03**: System assigns one of four matching states to each comparison: matched, likely-match-needs-review, new-candidate, or conflict
- [ ] **DISC-04**: User can review candidate matches in a human-in-the-loop workflow showing existing record vs candidate with evidence chips (name similarity, distance, type agreement, source evidence)
- [ ] **DISC-05**: Reviewer can accept (add to registry), link (merge with existing), or reject (mark as false positive) each candidate
- [ ] **DISC-06**: System displays confidence levels (HIGH/MEDIUM/LOW) on AI-inferred attributes based on evidence agreement across sources

### Inspection & Risk

- [ ] **RISK-01**: System computes a risk-informed inspection interval for each structure using a semi-quantitative model: condition score × consequence factor × seasonal modifier × data staleness modifier
- [ ] **RISK-02**: System maps inspection urgency to legible intervals: 30 days, 90 days, 180 days, 12 months, 24 months, with emergency override
- [ ] **RISK-03**: System determines repair need using a blended condition score (0-100) with red-flag overrides for critical indicators (seepage, deformation, rapid erosion, repeated emergencies)
- [ ] **RISK-04**: System assigns one of four repair statuses: normal, inspection required, repair required, critical condition
- [ ] **RISK-05**: System prefers "inspection required" over false certainty when evidence is weak, stale, or conflicting
- [ ] **RISK-06**: User with engineer role can override system-recommended inspection intervals and repair statuses with logged provenance
- [ ] **RISK-07**: Administrator, engineer, inspector, and viewer roles have appropriate access permissions (RBAC)
- [ ] **RISK-08**: User can export structure lists as CSV/GeoJSON and generate inspection reports as PDF in all three languages

### Field Operations

- [ ] **FIELD-01**: Inspector can install the PWA on any device (desktop, mobile) and use it offline in the field
- [ ] **FIELD-02**: Inspector can capture photos, dictate voice notes (Kazakh or Russian), pin corrected coordinates, and fill inspection forms while offline
- [ ] **FIELD-03**: System syncs field captures when connectivity returns using deferred sync with field-level merge conflict resolution (not last-write-wins)
- [ ] **FIELD-04**: System transcribes voice notes to text post-sync using Kazakh and Russian speech-to-text APIs
- [ ] **FIELD-05**: Inspector can see per-record sync status (pending / syncing / confirmed / failed) and resolve conflicts via review UI

### AI & Search

- [ ] **AI-01**: User can ask natural-language questions about structures ("Why is this structure marked repair required?", "Show similar incidents in this basin", "Summarize all inspections since 2022")
- [ ] **AI-02**: AI copilot provides evidence-grounded answers with explicit source citations (inspection records, registry rows, OSM ways, document references)
- [ ] **AI-03**: AI copilot uses hybrid search: PostgreSQL full-text + pg_trgm (structured) + pgvector semantic similarity (unstructured) in a single query
- [ ] **AI-04**: AI copilot never makes final engineering decisions — it retrieves and synthesizes evidence; humans confirm all condition assignments
- [ ] **AI-05**: AI copilot supports trilingual queries (Russian, Kazakh, English)

### Integration

- [ ] **INT-01**: System exposes OGC API Features (Part 1 Core, Part 3 Filtering/CQL2) and OGC API Tiles (Part 1 Core) via TiPG for external GIS clients (QGIS, ArcGIS, government systems)
- [ ] **INT-02**: System maintains a STAC catalog for Earth observation evidence (Sentinel-2 scenes, water index composites) with TiTiler dynamic raster serving from COGs
- [ ] **INT-03**: System exposes a REST API for the application frontend (CRUD, search, copilot, ingestion, sync endpoints)
- [ ] **INT-04**: System separates imagery evidence (STAC/COG in MinIO) from structure features (PostGIS) per the architecture principle

### UI & i18n

- [ ] **UI-01**: User interface is fully trilingual (Russian, Kazakh, English) with language switching that preserves data values in source language
- [ ] **UI-02**: UI renders Kazakh-specific Cyrillic characters correctly using cyrillic-ext font subset (ә, ғ, қ, ң, ө, ұ, ү, h, і)
- [ ] **UI-03**: UI displays confidence badges and provenance source chips on all AI-inferred and externally-sourced attributes

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Future Expansion

- **FUTURE-01**: Expand to other oblasts beyond Zhambyl (national rollout)
- **FUTURE-02**: Real-time IoT sensor integration for automated monitoring
- **FUTURE-03**: Full InSAR deformation processing pipeline (Sentinel-1 SAR)
- **FUTURE-04**: Real-time alerting and emergency action plan management
- **FUTURE-05**: Complex hydraulic modeling (EPANET/SWMM) for canal capacity analysis
- **FUTURE-06**: Kazakh Latin script support (transition target 2031)
- **FUTURE-07**: Integration with National Water Resources Information System (launching end 2026)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time IoT sensor integration | Requires hardware deployment, telemetry infrastructure — different product category. Data model accommodates sensor provenance for future. |
| Full InSAR deformation processing | Compute-heavy research pipeline, not a product feature. Show roadmap placeholder only. |
| Native mobile apps (iOS/Android) | PWA covers cross-platform from single codebase. App store cycles delay updates. 2-3 person team can't maintain 3 codebases. |
| Autonomous AI condition assignment | LLMs produce confident but unverifiable assessments. In dam safety, false certainty kills people. IBM research: 28% severe overclaims without grounding. |
| Public Nominatim-based geocoding | OSM Foundation policy restricts heavy use. Use cached lookups or self-hosted geocoder. |
| Real-time alerting / EAP management | Requires real-time data (sensors) which is out of scope. Kazhydromet and Emergency Situations Department handle this. |
| Complex hydraulic modeling (EPANET/SWMM/MIKE 11) | Different domain requiring calibrated models, network topology. Kazvodhoz data lacks network topology. |
| Other oblasts beyond Zhambyl | Validate model in one oblast first. National expansion is political/data-governance challenge, not just technical. |
| Black-box CV model for structure detection | Requires labeled training data (doesn't exist for Kazakhstan), GPU compute, opaque results. Evidence-fusion is more credible and debuggable. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MAP-01 | — | Pending |
| MAP-02 | — | Pending |
| MAP-03 | — | Pending |
| MAP-04 | — | Pending |
| MAP-05 | — | Pending |
| DATA-01 | — | Pending |
| DATA-02 | — | Pending |
| DATA-03 | — | Pending |
| DATA-04 | — | Pending |
| DATA-05 | — | Pending |
| DATA-06 | — | Pending |
| DATA-07 | — | Pending |
| DATA-08 | — | Pending |
| DISC-01 | — | Pending |
| DISC-02 | — | Pending |
| DISC-03 | — | Pending |
| DISC-04 | — | Pending |
| DISC-05 | — | Pending |
| DISC-06 | — | Pending |
| RISK-01 | — | Pending |
| RISK-02 | — | Pending |
| RISK-03 | — | Pending |
| RISK-04 | — | Pending |
| RISK-05 | — | Pending |
| RISK-06 | — | Pending |
| RISK-07 | — | Pending |
| RISK-08 | — | Pending |
| FIELD-01 | — | Pending |
| FIELD-02 | — | Pending |
| FIELD-03 | — | Pending |
| FIELD-04 | — | Pending |
| FIELD-05 | — | Pending |
| AI-01 | — | Pending |
| AI-02 | — | Pending |
| AI-03 | — | Pending |
| AI-04 | — | Pending |
| AI-05 | — | Pending |
| INT-01 | — | Pending |
| INT-02 | — | Pending |
| INT-03 | — | Pending |
| INT-04 | — | Pending |
| UI-01 | — | Pending |
| UI-02 | — | Pending |
| UI-03 | — | Pending |

**Coverage:**
- v1 requirements: 44 total
- Mapped to phases: 0
- Unmapped: 44 ⚠️

---
*Requirements defined: 2026-06-25*
*Last updated: 2026-06-25 after initial definition*
