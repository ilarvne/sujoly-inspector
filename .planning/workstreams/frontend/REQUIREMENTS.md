# Requirements: SuJoly Inspector — Frontend

**Defined:** 2026-06-25
**Workstream:** frontend
**Core Value:** Users see every hydraulic structure on an interactive map with its digital passport, risk status, and inspection urgency — working online and offline, in Russian, Kazakh, and English.

## v1 Requirements

### Map & Visualization

- [ ] **MAP-01**: User can view an interactive map displaying all hydraulic structures, hydrological stations, and related facilities in Zhambyl Oblast
- [ ] **MAP-02**: User can see structure status visualization on the map via color-coded symbology (four-state condition: normal / inspection required / repair required / critical)
- [ ] **MAP-03**: User can click any structure on the map to open its digital passport
- [ ] **MAP-04**: Decision-maker can view a portfolio dashboard with condition distribution, repair queue, inspection coverage, and geographic distribution heatmap
- [ ] **MAP-05**: User can filter map and dashboard by district, basin, structure type, condition, and inspection status

### Data & Passport (UI)

- [ ] **DATA-04**: User can view a digital passport per structure showing identity, type, geometry, administrative location, technical specifications, current status, and source provenance
- [ ] **DATA-05-FE**: User can view inspection history timeline per structure (date, inspector, findings, photos, condition at time of inspection)
- [ ] **DATA-06-FE**: User can attach documents (scanned passports, inspection reports, photos) to structure records via upload UI

### Discovery & Matching (UI)

- [ ] **DISC-04**: User can review candidate matches in a human-in-the-loop workflow showing existing record vs candidate with evidence chips (name similarity, distance, type agreement, source evidence)

### Inspection & Risk (UI)

- [ ] **RISK-06-FE**: User with engineer role can override system-recommended inspection intervals and repair statuses via UI with logged provenance
- [ ] **RISK-07-FE**: UI enforces role-appropriate access (administrator, engineer, inspector, viewer) with login and permission gating
- [ ] **RISK-08-FE**: User can export structure lists as CSV/GeoJSON and generate inspection reports as PDF from the UI in all three languages

### Field Operations

- [ ] **FIELD-01**: Inspector can install the PWA on any device (desktop, mobile) and use it offline in the field
- [ ] **FIELD-02**: Inspector can capture photos, dictate voice notes (Kazakh or Russian), pin corrected coordinates, and fill inspection forms while offline
- [ ] **FIELD-03**: System syncs field captures when connectivity returns using deferred sync with field-level merge conflict resolution (not last-write-wins)
- [ ] **FIELD-04**: System transcribes voice notes to text post-sync using Kazakh and Russian speech-to-text APIs
- [ ] **FIELD-05**: Inspector can see per-record sync status (pending / syncing / confirmed / failed) and resolve conflicts via review UI

### AI & Search (UI)

- [ ] **AI-01**: User can ask natural-language questions about structures ("Why is this structure marked repair required?", "Show similar incidents in this basin", "Summarize all inspections since 2022")
- [ ] **AI-02**: AI copilot provides evidence-grounded answers with explicit source citations (inspection records, registry rows, OSM ways, document references) displayed as clickable references
- [ ] **AI-05**: AI copilot supports trilingual queries (Russian, Kazakh, English)

### UI & i18n

- [ ] **UI-01**: User interface is fully trilingual (Russian, Kazakh, English) with language switching that preserves data values in source language
- [ ] **UI-02**: UI renders Kazakh-specific Cyrillic characters correctly using cyrillic-ext font subset (ә, ғ, қ, ң, ө, ұ, ү, h, і)
- [ ] **UI-03**: UI displays confidence badges and provenance source chips on all AI-inferred and externally-sourced attributes

## Out of Scope (Frontend)

| Feature | Reason |
|---------|--------|
| Database schema / PostGIS | Handled by backend workstream |
| Risk score calculation logic | Handled by backend workstream |
| OGC API / TiPG configuration | Handled by backend workstream |
| RAG agent / LangGraph | Handled by backend workstream |
| Data ingestion pipelines | Handled by backend workstream |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| UI-01 | Phase 1 | Pending |
| UI-02 | Phase 1 | Pending |
| MAP-01 | Phase 2 | Pending |
| MAP-02 | Phase 2 | Pending |
| MAP-03 | Phase 2 | Pending |
| MAP-04 | Phase 2 | Pending |
| MAP-05 | Phase 2 | Pending |
| DATA-04 | Phase 2 | Pending |
| DATA-05-FE | Phase 3 | Pending |
| DATA-06-FE | Phase 3 | Pending |
| RISK-06-FE | Phase 3 | Pending |
| RISK-07-FE | Phase 3 | Pending |
| RISK-08-FE | Phase 3 | Pending |
| DISC-04 | Phase 4 | Pending |
| UI-03 | Phase 4 | Pending |
| FIELD-01 | Phase 5 | Pending |
| FIELD-02 | Phase 5 | Pending |
| FIELD-03 | Phase 5 | Pending |
| FIELD-04 | Phase 5 | Pending |
| FIELD-05 | Phase 5 | Pending |
| AI-01 | Phase 6 | Pending |
| AI-02 | Phase 6 | Pending |
| AI-05 | Phase 6 | Pending |

**Coverage:** 23 requirements mapped to 6 phases

---
*Requirements defined: 2026-06-25*
*Last updated: 2026-06-25 after workstream split*
