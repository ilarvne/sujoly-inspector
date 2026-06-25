# Zhambyl Hydraulic Structures Catalog

## What This Is

A web-first, installable PWA that serves as the digital operating layer for hydraulic structures in Zhambyl Oblast, Kazakhstan. It ingests legacy registry data, discovers candidate structures from open sources and satellite imagery, compares them against the existing database, computes risk-informed inspection intervals and repair priorities, and gives inspectors and decision-makers a map-first, evidence-backed workflow. The system is trilingual (Russian, Kazakh, English) and designed for both office analytics and offline field use.

## Core Value

Every hydraulic structure in Zhambyl has one canonical, evidence-backed record visible on an interactive map with its current condition, inspection urgency, and repair status — enabling data-driven maintenance decisions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Interactive map displaying hydraulic structures, hydrological stations, and related facilities with status visualization
- [ ] Digital passport per structure: identity, type, geometry, location, technical specs, inspection history, attached documents, current status, source provenance
- [ ] Data ingestion from multiple sources: Kazvodhoz canal registry spreadsheet, OpenStreetMap, satellite imagery, scanned passports (OCR)
- [ ] Algorithm for locating hydraulic structures using evidence-fusion (OSM tags, hydrography, satellite water indices, document mentions)
- [ ] Algorithm for comparing found objects with existing database (hierarchical multilingual matching with matched / likely-match-needs-review / new-candidate / conflict taxonomy)
- [ ] Model for inspection interval assessment (risk-informed: condition, last inspection date, age, accident rate, importance, seasonal factors)
- [ ] Model for repair need determination (normal / inspection required / repair required / critical condition)
- [ ] Analytical metrics and dashboards for technical condition across the portfolio
- [ ] Trilingual UI (Russian, Kazakh, English)
- [ ] Integration capability via open standards (OGC API Features/Tiles, STAC, REST API)
- [ ] Field mode: offline PWA capture with photo, voice note transcription, coordinate correction, and deferred sync
- [ ] AI copilot: evidence-grounded Q&A about structures with source citations (hybrid search over Postgres + Milvus)
- [ ] Confidence and provenance tracking on every fact and status
- [ ] Human-in-the-loop review workflow for candidate verification (accept / link to existing / reject)

### Out of Scope

- Real-time IoT sensor integration — defer to future phase; current data is registry-based
- Full InSAR deformation processing pipeline — show roadmap/placeholder only; too compute-heavy for initial build
- Mobile native apps (iOS/Android) — PWA covers cross-platform from single codebase
- Public Nominatim-based geocoding as embedded service — OSM Foundation policy restricts this; use cached lookups or self-hosted geocoder
- Autonomous AI condition assignment — LLMs never make final engineering decisions; all recommendations are evidence-backed and human-reviewed
- Other oblasts beyond Zhambyl for initial release — focus on one region to prove the model

## Context

**Domain context:**
Kazakhstan is actively digitizing hydraulic infrastructure. In 2025, government reporting indicated 1,395 hydraulic structures were examined before flood season with 560 requiring repair. The country is reconstructing 115 canals with digitalization elements across six regions including Zhambyl. Kazhydromet already operates an interactive hydrological monitoring map with 377 observation points, proving that map-centric interaction is familiar and credible in this context. A 2026 academic paper on GIS for dam monitoring in Kazakhstan argues that global datasets are too general for national needs and that meaningful systems must preserve monitoring history and unify heterogeneous observation data.

**Data on hand:**
Kazvodhoz canal registry spreadsheet — technical characteristics of all canals operated by RGP "Kazvodhoz" branches. Contains: commissioning year, water source, carrying capacity (m³/s), total length (km) before/after reconstruction, earthwork vs lined length, suspended area (ha), KPD (efficiency) projected vs actual, serviced districts, rural district location, wear percentage, technical condition, cadastral number, state act. Data is in Russian.

**Team:** 2-3 people, ongoing project (not time-boxed).

**Strategic positioning:**
The winning product story is "we built the digital operating layer for hydraulic structures" — not a flashy AI demo. The system should feel deployable on Monday: credible, standards-compliant, evidence-backed, human-reviewable.

## Constraints

- **Tech stack**: Next.js PWA + MapLibre GL JS (frontend), FastAPI + PostgreSQL/PostGIS (backend), TiPG (vector tiles API), TiTiler + STAC/COG + MinIO (raster/imagery), Redis (caching/job queues), Milvus (vector similarity search), LangGraph (workflow orchestration) — chosen for standards compliance, demo reliability, and integration capability
- **Languages**: Trilingual UI required — Russian, Kazakh, English. Data sources are primarily in Russian.
- **Data sources**: Starting with Kazvodhoz spreadsheet only; OSM, satellite imagery, and other sources to be integrated during build
- **Standards**: OGC API Features/Tiles for vector access, STAC for EO metadata, S3-compatible MinIO for binary assets — required for integration deliverable
- **Architecture principle**: Every structure has one canonical asset record, many evidence sources, and a time-based condition history. PostGIS is the system of record. LLMs never make final engineering decisions.
- **Offline capability**: PWA with service workers for field inspection work without connectivity

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PWA over native mobile apps | Single codebase, installable, offline support via service workers — satisfies "web portal/website/mobile app" requirement without team split | — Pending |
| PostGIS as system of record (not Milvus) | PostgreSQL provides full-text search, pg_trgm fuzzy matching, spatial indexing — Milvus only for semantic/multimodal retrieval | — Pending |
| TiPG over GeoServer as primary geo API | Lightweight, FastAPI-based, OGC API Features/Tiles directly from PostGIS — GeoServer only as fallback for legacy WMS/WFS | — Pending |
| Evidence-fusion locator over CV detector | Combining OSM tags, hydrography, satellite water indices, and document mentions is more credible and debuggable than a from-scratch computer vision model | — Pending |
| Four-state matching taxonomy | matched / likely-match-needs-review / new-candidate / conflict — more operationally honest than binary match/no-match | — Pending |
| Semi-quantitative risk index over black-box ML for inspection intervals | Defensible, explainable, aligns with international dam safety practice (World Bank, FEMA/FERC) | — Pending |
| Condition score + red-flag overrides for repair status | Blended score with explicit critical triggers (seepage, deformation, rapid erosion) — safer than pure scoring, avoids false certainty | — Pending |
| STAC for EO evidence only, not for all structures | Structures belong in PostGIS as features; imagery belongs in STAC/COG — clean separation shows maturity | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-25 after initialization*
