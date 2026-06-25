# Feature Research

**Domain:** Geospatial hydraulic infrastructure / dam safety / water asset management portal
**Researched:** 2026-06-25
**Confidence:** HIGH

## Feature Landscape

Research surveyed commercial dam safety platforms (Dam360/ADASA, DamData/OFITECO, DamWatch/USEngineering, Sysdam, KISTERS WISKI), water utility asset management systems (AquaTwin, Autodesk InfoAsset Manager, AssetLab, GISWater, 1Spatial 1Water, ArcGIS Solutions), the Kazakhstan government digitization context (Kazhydromet interactive map, National Water Resources Information System, kazdams.kz), international dam safety standards (World Bank Risk Index, FEMA/FERC RIDM, USBR SQRA), AI copilot patterns for industrial assets (Nlyte, Qarion, AssetOpsBench/IBM, IndustryAssetEQA), OGC API standards (Features, Tiles, STAC), provenance frameworks (W3C PROV, GeoPROV, attestation models), and PWA offline-first field collection patterns.

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete. In this domain, the bar is set by Kazhydromet's existing interactive hydrological monitoring map (377 observation points, daily updates, flood predictors) and the kazdams.kz dam monitoring GIS already under development in Kazakhstan. Government stakeholders have seen map-centric infrastructure portals; they expect them.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Interactive map with structure status visualization | Kazhydromet already operates an interactive hydrological monitoring map (ecodata.kz). Every competitor (Dam360, DamWatch, ArcGIS Dam Safety, kazdams.kz) leads with a map. A hydraulic structures portal without a map is unthinkable. | MEDIUM | MapLibre GL JS + TiPG vector tiles from PostGIS. Status visualization via symbology (condition colors, inspection urgency icons). Basemap + structure layer + hydrological stations layer. Click-to-open passport. This is the primary entry point. |
| Digital passport per structure | Every dam safety system has a "dam file" or "asset record." The Indonesian Cengklik reservoir database model, USACE NID, Virginia DSIS, and kazdams.kz all center on a per-structure record containing identity, type, geometry, technical specs, inspection history, documents, and current status. PROJECT.md calls this the "canonical asset record." | MEDIUM | PostGIS feature with rich attribute model. Tabs/sections: identity, geometry/location, technical specifications, inspection history, attached documents, condition timeline, provenance/source links. Must support multilingual field labels (RU/KK/EN) while preserving source-language data values. |
| Structure inventory / registry | The USACE National Inventory of Dams, Virginia DSIS, and all asset management systems start with an inventory. Kazvodhoz already maintains a canal registry spreadsheet. Without a complete inventory, nothing else functions. | LOW (ingestion) / MEDIUM (data quality) | Ingest Kazvodhoz spreadsheet as initial seed. Each structure gets a stable internal ID. The inventory must handle incomplete records gracefully — many structures will have missing coordinates, missing commissioning dates, or wear percentages that need validation. |
| Condition status display (normal / inspection required / repair required / critical) | Every competitor displays condition. The US NID has CONDITION_ASSESSMENT. The Kazakh government reported 560 of 1,395 HES requiring repair, 540 unsatisfactory, 20 emergency. Decision-makers need to see this at a glance. | MEDIUM | Four-state model per PROJECT.md decision. Blended condition score with explicit red-flag overrides (seepage, deformation, rapid erosion). The condition must be human-assigned or human-confirmed — LLMs never make final engineering decisions (PROJECT.md constraint). |
| Inspection history timeline | Dam360, DamData, Oxmaint, KISTERS FieldVisits, Sysdam, and ArcGIS Dam Safety all track inspection records over time. FERC Part 12 requires unbroken, timestamped inspection history. Without history, there's no basis for risk-informed intervals. | MEDIUM | Chronological list of inspection events per structure. Each event: date, inspector, findings, photos, condition assessment at time of inspection. Timeline visualization showing condition changes over time. This is the temporal backbone of the system. |
| Search and filter structures | Every inventory system has search. Users need to find structures by name, type, condition, district, or location. Virginia DSIS, ArcGIS solutions, and all CMMS platforms provide filtering. | LOW | Full-text search (PostgreSQL tsvector for Russian/Kazakh/English), attribute filters (condition, type, district, inspection status), spatial filters (bbox, within-district). pg_trgm for fuzzy matching on multilingual names. |
| Trilingual UI (Russian / Kazakh / English) | Non-negotiable per PROJECT.md. Kazakhstan is actively digitizing in trilingual context. Government systems must serve Kazakh-speaking citizens, Russian-speaking engineers, and English-speaking international partners. | MEDIUM | i18n framework (next-intl or similar). All UI strings in three languages. Data values preserved in source language with display-language fallback. Especially important: structure names may be in Russian only (from Kazvodhoz data), but labels and navigation must switch. Cyrillic text rendering and search must work correctly. |
| Document attachment per structure | Dam360, DamData, DamWatch all store documents (inspection reports, EAPs, design drawings, scanned passports). The Kazvodhoz registry references cadastral numbers and state acts — documents that must be attached. | LOW-MEDIUM | File upload to MinIO (S3-compatible). Link documents to structure records with metadata (document type, date, source, language). OCR for scanned passports is a differentiator (see below); basic attachment is table stakes. |
| Portfolio dashboard / analytics | AquaTwin, AssetLab, Sysdam BI module, ArcGIS Dashboards, and Autodesk InfoAsset all provide portfolio-level views. The Kazakh government needs aggregate reporting: how many structures need repair, condition distribution, inspection coverage. | MEDIUM | Dashboard with: condition distribution (pie/bar), inspection overdue count, repair queue by priority, geographic distribution heatmap. Filters by district, structure type, condition. This is what decision-makers see first. |
| Role-based access control | DamData, Sysdam, DamWatch, Virginia DSIS, and ArcGIS Solutions all implement role-based permissions. Inspectors, engineers, administrators, and public viewers need different access levels. | MEDIUM | Roles: administrator (full access), engineer (edit structures, inspections), inspector (field data entry, read passports), viewer (read-only map + public data). Project-scoped permissions per PROJECT.md architecture. |
| Export / reporting | Every compliance-driven system generates reports. FERC Part 12 requires retrievable audit records. Kazakh government reporting needs exportable condition summaries. | LOW-MEDIUM | Export structure lists as CSV/GeoJSON. Generate inspection reports as PDF. Portfolio summary reports. Export must work in all three languages. |

### Differentiators (Competitive Advantage)

Features that set this product apart from existing dam safety and asset management systems. These align with PROJECT.md's Core Value: "the digital operating layer for hydraulic structures" — credible, standards-compliant, evidence-backed, human-reviewable. The differentiators are not "more features" but "smarter, more transparent, more interoperable."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Evidence-fusion candidate discovery from satellite/OSM/documents | No competitor combines OSM tags, hydrography, satellite water indices (NDWI, MNDWI from Sentinel-2), and document mentions to discover hydraulic structures that are missing from registries. GeoAI4Water (HeiGIT) and IGraSS (IJCAI 2025) prove the approach works for water infrastructure, but no commercial product ships it. This finds the "unknown unknowns" — structures that exist but aren't in any database. | HIGH | LangGraph workflow orchestrating: OSM tag query (waterway/dam/canal tags), hydrography intersection, Sentinel-2 water index computation (via TiTiler/COG), and document OCR/matching. Candidates are NOT auto-added — they go through human-in-the-loop review. Evidence fusion is more credible and debuggable than a black-box CV model (PROJECT.md decision). |
| Four-state matching taxonomy (matched / likely-match-needs-review / new-candidate / conflict) | Binary match/no-match is operationally dishonest. Dam safety data is messy: the same canal may appear in Kazvodhoz with slightly different coordinates, in OSM with a different name, and in a scanned passport with an old identifier. The four-state taxonomy makes uncertainty explicit and actionable. No competitor does this. | HIGH | Hierarchical multilingual matching: spatial proximity → name similarity (pg_trgm across RU/KK/EN) → attribute comparison → confidence scoring. "Conflict" state is critical — it surfaces cases where sources disagree (e.g., different condition assessments) for human resolution. This is the data quality engine. |
| Risk-informed inspection interval assessment (semi-quantitative) | Most dam safety systems use fixed inspection cycles (FERC: 5-year for Part 12, 10-year for comprehensive). The World Bank Risk Index methodology, FEMA/FERC RIDM, and USBR SQRA all support risk-informed prioritization. Computing a defensible, explainable inspection interval based on condition, age, last inspection date, accident rate, importance, and seasonal factors is more sophisticated than calendar-based scheduling. | HIGH | Semi-quantitative risk index (not black-box ML — PROJECT.md decision). Weighted factors: current condition score, years since last inspection, structure age, historical incident rate, downstream consequence/importance, seasonal flood exposure. Output: recommended inspection interval (e.g., 6 months / 1 year / 2 years / 5 years) with explanation of contributing factors. Aligns with World Bank portfolio risk assessment practice. Must be defensible to engineers. |
| Repair need determination with red-flag overrides | Blended condition scoring alone is dangerous — a structure can score "fair" overall but have a critical seepage issue. The red-flag override system (seepage, deformation, rapid erosion → automatically "repair required" or "critical") is safer than pure scoring and avoids false certainty. This is more nuanced than competitors' single-status fields. | MEDIUM | Condition score (0-100 or categorical) computed from inspection findings. Red-flag triggers override to "repair required" or "critical" regardless of score. Red-flags are specific engineering indicators, not arbitrary thresholds. The override is logged with provenance (which inspection, which finding triggered it). |
| AI copilot with evidence-grounded Q&A and source citations | Nlyte, Qarion, and IBM's AssetOpsBench demonstrate that natural-language Q&A over infrastructure data is valuable but must be grounded in verified data. IBM's IndustryAssetEQA (ACL 2026) shows that neurosymbolic grounding reduces expert-rated overclaims from 28% to 2%. The copilot answers questions like "Which structures in Merke district haven't been inspected in 3+ years?" or "What's the condition history of Canal X?" with citations to specific inspection records, source documents, and database entries. | HIGH | Hybrid search: Postgres full-text + pg_trgm (structured queries) + Milvus vector similarity (semantic/multimodal retrieval). LangGraph orchestration. Every answer cites sources: [inspection #123, 2024-06-15], [Kazvodhoz registry row 45], [OSM way 123456]. LLM never makes engineering decisions — it retrieves and synthesizes evidence. The copilot is a research assistant, not an engineer. |
| Provenance tracking on every fact and status | No competitor tracks provenance at the fact/attribute level. Most track it at the dataset level (metadata). The W3C PROV standard, GeoPROV (semantic web journal, 2025), and the attestation model (World Historical Gazetteer) demonstrate that fact-level provenance is achievable and valuable. "This condition assessment came from Inspector Smith's field report on 2024-06-15, cross-referenced with Kazvodhoz registry data" is far more credible than an unattributed status field. | HIGH | Every attribute on every structure has a provenance record: source type (Kazvodhoz / OSM / satellite / field inspection / AI inference / document OCR), source reference, confidence level, timestamp, contributor. Implemented as an attestation/edge model linking facts to sources. This is the trust infrastructure. |
| Human-in-the-loop review workflow for candidate verification | The four-state matching taxonomy produces "likely-match-needs-review" and "new-candidate" items that need human judgment. The review workflow (accept / link to existing / reject) with evidence display is what makes the system credible. Without it, the system is an opaque auto-matcher. With it, the system is an evidence-backed decision support tool. | MEDIUM | Review queue UI: shows candidate, shows matched existing structure (if any), shows all evidence (OSM tags, satellite imagery, document mentions, spatial proximity). Reviewer can accept (add to registry), link (merge with existing), or reject (mark as false positive). Review decision is logged with provenance. |
| OGC API Features/Tiles compliance | Standards compliance is the integration deliverable. TiPG provides OGC API Features Part 1 (Core), Part 3 (Filtering/CQL2), and Tiles Part 1 (Core) directly from PostGIS. This means any OGC-compliant client (QGIS, ArcGIS, other government systems) can consume the data. Kazakhstan's National Water Resources Information System (launching end of 2026) will need integration points — OGC APIs are those points. | MEDIUM | TiPG as the geo API layer. Collections for structures, hydrological stations, candidates. Vector tiles via OGC API Tiles. Conformance endpoint for validation. This is not a feature users see, but it's what makes the system a "digital operating layer" rather than a silo. |
| STAC catalog for Earth observation evidence | STAC (OGC Community Standard 25-004, v1.1.0) is the standard for satellite imagery metadata. Using STAC for EO evidence (Sentinel-2 scenes used for water index computation, historical imagery for change detection) separates imagery evidence from structure features cleanly. PROJECT.md decision: "structures belong in PostGIS as features; imagery belongs in STAC/COG." No dam safety competitor uses STAC. | MEDIUM | TiTiler for dynamic raster rendering from COGs stored in MinIO. STAC API for temporal/spatial search of imagery. Each satellite scene used as evidence gets a STAC Item linked to the structure's provenance. Users can click "view satellite evidence" and see the actual imagery that informed a candidate discovery. |
| Offline PWA field mode with deferred sync | Dam360, DamData, Sysdam, and KISTERS FieldVisits all offer offline mobile data collection — but as native apps. A PWA with offline capability (service worker cache, IndexedDB queue, background sync) achieves the same from a single codebase. Research shows this pattern is production-proven: utility field service PWAs, waste audit platforms, and inspection systems all successfully use service worker + IndexedDB + sync queue with conflict resolution. | HIGH | Service worker caches app shell + assigned inspections + reference data. IndexedDB stores field captures (photos, voice notes, coordinates, form data). Sync queue with idempotency keys. Per-record sync status (pending / syncing / confirmed / failed). Conflict resolution via entry timestamps. GPS coordinate correction. Voice note transcription (online, post-sync). This is the hardest engineering feature in the system. |
| Confidence scoring on AI-inferred attributes | When the evidence-fusion locator infers a structure's type or when OCR extracts data from a scanned passport, the result has uncertainty. Displaying confidence levels (HIGH/MEDIUM/LOW) on AI-inferred attributes is more honest than presenting them as facts. No competitor does this systematically. | MEDIUM | Confidence = function of evidence agreement (multiple sources agree → HIGH; single source → MEDIUM; conflicting sources → LOW with conflict flag). Confidence is part of the provenance record. UI shows confidence badges on inferred attributes. Low-confidence items surface in review queues. |
| Multilingual matching across data sources | Structure names in Kazvodhoz are in Russian. OSM may have names in English, Kazakh, or transliterated forms. Scanned passports may be in Russian or Kazakh. Matching across these requires multilingual fuzzy matching (pg_trgm + transliteration + dictionary lookups). This is specific to the trilingual Kazakhstan context and no international competitor handles it. | HIGH | Transliteration pipelines (Cyrillic ↔ Latin). Bilingual dictionaries (RU↔KK geographic terms: "канал" ↔ "канал" ↔ "canal", "плотина" ↔ "бөгет" ↔ "dam"). pg_trgm similarity scoring across transliterated forms. This is essential for the matching taxonomy to work in practice. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems. These are explicitly out of scope per PROJECT.md or would undermine the product's credibility.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time IoT sensor integration | "Modern dam safety systems have SCADA/sensor integration" — Dam360, DamData, KISTERS all showcase real-time sensor feeds. | Kazakhstan's current data is registry-based, not sensor-based. Kazhydromet's 377 stations are mostly manual. IoT integration requires hardware deployment, telemetry infrastructure, and real-time alerting — massive scope expansion for a 2-3 person team. It also shifts the product from "digital operating layer" to "SCADA monitoring," which is a different product with different stakeholders. | Design the data model to accommodate sensor data (provenance source type: "sensor"), but don't build ingestion pipelines. Show a roadmap placeholder. The National Water Resources Information System is automating 103 canals with gate sensors — that's their job, not ours. |
| Full InSAR deformation processing pipeline | "Satellite-based deformation monitoring is cutting-edge" — Talgarbayeva et al. (2025) demonstrated InSAR for earth dam deformation in Kazakhstan's seismically active regions. | InSAR processing is compute-heavy (requires SAR scene pairs, persistent scatterer processing, deformation time series). It's a research pipeline, not a product feature. Including it would consume the team's capacity for minimal initial value. | Use Sentinel-1/Sentinel-2 imagery as evidence (STAC catalog, water indices) but don't run InSAR processing. Show a roadmap item for future deformation monitoring. The kazdams.kz project is already exploring this. |
| Autonomous AI condition assignment | "The AI should automatically assess structure condition from photos and data" — tempting because it would reduce manual inspection workload. | LLMs and CV models produce confident but unverifiable assessments. In dam safety, false certainty kills people. IBM's IndustryAssetEQA research shows LLM-only baselines have 28% severe overclaims. PROJECT.md explicitly states: "LLMs never make final engineering decisions; all recommendations are evidence-backed and human-reviewed." | AI copilot provides evidence-grounded recommendations and highlights patterns, but a human engineer confirms every condition assignment. The system surfaces evidence; the human makes the call. |
| Public Nominatim-based geocoding as embedded service | "Use OSM's free geocoding to find structure addresses" — seems like a quick win for location search. | OSM Foundation's usage policy explicitly restricts heavy use of the public Nominatim instance. Embedding it in a production government portal violates the policy and is unreliable. | Cache OSM geocoding results locally, or self-host a Nominatim/Pelias instance with Kazakhstan OSM extract. Use PostGIS for spatial queries (structures already have coordinates). Geocoding is a convenience, not a core feature. |
| Native mobile apps (iOS/Android) | "Inspectors need a native app for field work" — Dam360, DamData, KISTERS all ship native mobile apps. | Maintaining two native codebases plus a web app with a 2-3 person team is unsustainable. App store approval cycles delay updates. PWA technology (service workers, IndexedDB, background sync, installable, push notifications) now covers the gap. Research confirms production PWA field platforms work reliably offline. | PWA with offline-first architecture. Installable on any device. Single codebase. Updates deploy instantly. This is a PROJECT.md key decision. |
| Other oblasts beyond Zhambyl | "Scale to all of Kazakhstan from day one" — the government has 1,395 structures nationwide. | Scaling before validating the model in one oblast risks building the wrong thing at scale. Zhambyl has the data (Kazvodhoz spreadsheet), the context (flood-prone, canal reconstruction), and the scale to prove the concept. National rollout is a political and data-governance challenge, not just a technical one. | Focus on Zhambyl for initial release. Design the architecture to be oblast-agnostic (district/region as a filter dimension). National expansion is a v2 milestone after validating in Zhambyl. |
| Black-box computer vision model for structure detection | "Train a CV model to detect dams from satellite imagery" — GeoAI4Water and IGraSS show it's possible. | A from-scratch CV model requires labeled training data (which doesn't exist for Kazakhstan hydraulic structures), GPU compute, and produces opaque results. The evidence-fusion approach (OSM + hydrography + water indices + documents) is more credible, debuggable, and doesn't require training data. PROJECT.md explicitly chose this. | Evidence-fusion locator combining multiple weak signals into strong candidates with explainable reasoning. Each candidate shows exactly which evidence contributed. |
| Real-time alerting / emergency action plan management | "The system should send SMS alerts when a dam is failing" — DamWatch, Dam360, and KISTERS all have alerting. | Real-time alerting requires real-time data (sensors, telemetry) which is out of scope. EAP management is a compliance workflow that belongs in a different system. Building half-baked alerting creates false confidence. | The system highlights structures in critical condition and overdue inspections (dashboard, priority queues). It does not claim to provide real-time safety monitoring. That's Kazhydromet's and the Emergency Situations Department's role. |
| Complex hydraulic modeling (EPANET/SWMM/MIKE 11) | "Integrate hydraulic simulation for canal capacity analysis" — GISWater, Autodesk InfoAsset, and AquaTwin all do this. | Hydraulic modeling is a different domain requiring calibrated models, network topology, and simulation expertise. The Kazvodhoz data has carrying capacity and KPD values but not network topology suitable for EPANET. This is scope creep into a different product category. | Display the technical specifications (carrying capacity, KPD, length) from the registry. Don't simulate. If hydraulic modeling is needed later, it's a separate integration via the OGC API. |

## Feature Dependencies

```
[Structure Inventory / Registry]
    └──requires──> [Data Ingestion Pipeline (Kazvodhoz spreadsheet)]
    └──enables──> [Interactive Map with Status Visualization]
                       └──enables──> [Digital Passport per Structure]
                                          └──enables──> [Inspection History Timeline]
                                          └──enables──> [Condition Status Display]
                                          └──enables──> [Document Attachment]

[Structure Inventory] ──enables──> [Search and Filter]
[Structure Inventory] ──enables──> [Portfolio Dashboard]

[Condition Status Display]
    └──requires──> [Inspection History Timeline]
    └──enables──> [Repair Need Determination with Red-Flag Overrides]
    └──enables──> [Risk-Informed Inspection Interval Assessment]

[Data Ingestion Pipeline]
    └──enables──> [Evidence-Fusion Candidate Discovery]
                       └──requires──> [STAC Catalog for EO Evidence]
                       └──requires──> [OGC API Features/Tiles Compliance]
                       └──enables──> [Four-State Matching Taxonomy]
                                          └──requires──> [Multilingual Matching]
                                          └──enables──> [Human-in-the-Loop Review Workflow]
                                          └──enables──> [Provenance Tracking on Every Fact]

[Provenance Tracking]
    └──enables──> [Confidence Scoring on AI-Inferred Attributes]
    └──enables──> [AI Copilot with Evidence-Grounded Q&A]
                       └──requires──> [Provenance Tracking]
                       └──requires──> [Structure Inventory + Passports + Inspections]

[Offline PWA Field Mode]
    └──requires──> [Digital Passport per Structure] (to know what to inspect)
    └──requires──> [Inspection History Timeline] (to add new inspections)
    └──enables──> [Condition Status Display] (field-collected conditions update status)

[Trilingual UI] ──parallel-to──> [all features] (applies everywhere, not a dependency)

[Role-Based Access Control] ──parallel-to──> [all features] (applies everywhere)

[Export / Reporting] ──requires──> [Portfolio Dashboard] + [Structure Inventory]
```

### Dependency Notes

- **Interactive Map requires Structure Inventory:** Cannot display what doesn't exist in the database. The Kazvodhoz ingestion is the critical path — everything starts with getting structures into PostGIS.
- **Digital Passport enables Inspection History:** The passport is the container; inspections are the temporal content within it. Build the container first.
- **Condition Status requires Inspection History:** You can't assign a current condition without inspection records to base it on. Even the initial Kazvodhoz "wear percentage" and "technical condition" fields are pseudo-inspection data.
- **Repair Determination + Risk Interval both require Condition Status:** These are analytical computations on top of condition data. They can't run until conditions exist.
- **Evidence-Fusion Discovery requires Data Ingestion + STAC:** Discovery compares new candidates against the existing registry. STAC provides the satellite imagery evidence layer. OGC APIs expose the data for the discovery workflow to query.
- **Four-State Matching requires Multilingual Matching:** The matching taxonomy is useless if it can't match "Канал Мерке" (Kazvodhoz) with "Merke Canal" (OSM) with "Меркі каналы" (Kazakh passport). Multilingual matching is the engine inside the taxonomy.
- **AI Copilot requires Provenance Tracking:** The copilot's value is evidence-grounded answers with citations. Without provenance, there's nothing to cite. This is why provenance must be built before or alongside the copilot.
- **Offline PWA requires Digital Passport + Inspection History:** Field inspectors need to see the passport (what to inspect) and add to the inspection history (what they found). The offline mode is the field interface to these core entities.
- **Trilingual UI and RBAC are cross-cutting:** They apply to every feature, not as dependencies but as quality attributes. They should be designed in from the start (i18n strings, role checks in API layer) rather than bolted on later.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept. The MVP must demonstrate the "digital operating layer" thesis: every structure has one canonical, evidence-backed record on a map with condition and inspection urgency.

- [ ] Data ingestion from Kazvodhoz spreadsheet → PostGIS — the seed data; without it, nothing exists
- [ ] Interactive map with structure status visualization (MapLibre + TiPG) — the primary interface; this is what stakeholders see first
- [ ] Digital passport per structure (identity, type, geometry, technical specs, current status) — the canonical record
- [ ] Condition status display (four-state model) — the decision-support output
- [ ] Trilingual UI (RU/KK/EN) — non-negotiable from day one
- [ ] Search and filter structures — basic navigability
- [ ] Provenance tracking on initial Kazvodhoz data — establishes the trust infrastructure from the start
- [ ] Portfolio dashboard (condition distribution, repair queue) — the executive view

**Rationale:** The MVP proves that registry data can become a credible, map-first, trilingual digital operating layer. It doesn't include discovery, AI, or offline field mode — those are enhancements that depend on the core existing. The MVP is "the Kazvodhoz spreadsheet, made credible and visible."

### Add After Validation (v1.x)

Features to add once core is working and stakeholders confirm the map + passport + condition model is right.

- [ ] Inspection history timeline — triggered by first real inspection data entry
- [ ] Document attachment per structure — triggered by need to attach scanned passports and reports
- [ ] Risk-informed inspection interval assessment — triggered by having enough inspection history to compute intervals
- [ ] Repair need determination with red-flag overrides — triggered by inspection findings with specific defect types
- [ ] OGC API Features/Tiles compliance — triggered by integration requirement (e.g., National Water Resources Information System)
- [ ] Human-in-the-loop review workflow — triggered by first candidate discovery run
- [ ] Role-based access control (beyond basic admin/viewer) — triggered by multiple user types in production

### Future Consideration (v2+)

Features to defer until product-market fit is established in Zhambyl.

- [ ] Evidence-fusion candidate discovery (OSM + satellite + documents) — complex, requires STAC + TiTiler + LangGraph; defer until core registry is stable
- [ ] STAC catalog for EO evidence — defer with discovery; they're a pair
- [ ] Four-state matching taxonomy + multilingual matching — depends on discovery producing candidates to match
- [ ] AI copilot with evidence-grounded Q&A — highest complexity differentiator; requires provenance + Milvus + LangGraph; defer until data volume justifies it
- [ ] Offline PWA field mode — highest engineering complexity; defer until office-based workflow is validated and field deployment is planned
- [ ] Confidence scoring on AI-inferred attributes — depends on AI features existing
- [ ] Export / reporting (advanced) — basic export in v1, compliance-grade reporting later
- [ ] Expansion to other oblasts — political and data-governance decision, not just technical

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Kazvodhoz data ingestion → PostGIS | HIGH | LOW | P1 |
| Interactive map with status visualization | HIGH | MEDIUM | P1 |
| Digital passport per structure | HIGH | MEDIUM | P1 |
| Condition status display (four-state) | HIGH | MEDIUM | P1 |
| Trilingual UI (RU/KK/EN) | HIGH | MEDIUM | P1 |
| Search and filter structures | HIGH | LOW | P1 |
| Provenance tracking (initial) | MEDIUM | MEDIUM | P1 |
| Portfolio dashboard | HIGH | MEDIUM | P1 |
| Inspection history timeline | HIGH | MEDIUM | P2 |
| Document attachment per structure | MEDIUM | LOW-MEDIUM | P2 |
| Risk-informed inspection intervals | HIGH | HIGH | P2 |
| Repair need with red-flag overrides | HIGH | MEDIUM | P2 |
| OGC API Features/Tiles compliance | MEDIUM | MEDIUM | P2 |
| Role-based access control (full) | MEDIUM | MEDIUM | P2 |
| Human-in-the-loop review workflow | HIGH | MEDIUM | P2 |
| Evidence-fusion candidate discovery | HIGH | HIGH | P3 |
| STAC catalog for EO evidence | MEDIUM | MEDIUM | P3 |
| Four-state matching taxonomy | HIGH | HIGH | P3 |
| Multilingual matching | HIGH | HIGH | P3 |
| AI copilot with evidence Q&A | HIGH | HIGH | P3 |
| Offline PWA field mode | HIGH | HIGH | P3 |
| Confidence scoring on AI attributes | MEDIUM | MEDIUM | P3 |
| Export / reporting (advanced) | MEDIUM | LOW-MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch — the MVP
- P2: Should have, add when core is validated — the v1.x expansion
- P3: Nice to have, future consideration — the v2+ differentiators

## Competitor Feature Analysis

| Feature | Dam360 / DamData (commercial dam safety) | ArcGIS Dam Safety (Esri) | kazdams.kz (Kazakhstan academic) | Kazhydromet interactive map | Our Approach |
|---------|------------------------------------------|--------------------------|----------------------------------|------------------------------|--------------|
| Interactive map | SCADA view + GIS + BIM | ArcGIS Online map + Dashboard | Web GIS map | Interactive hydrological monitoring map | MapLibre + TiPG vector tiles from PostGIS — open standards, no proprietary platform |
| Digital passport | Dam file with all data | Feature attributes in ArcGIS | Dam passport module | Post/station info table | Rich PostGIS feature with provenance per attribute — fact-level traceability |
| Inspection scheduling | Configurable route inspections + scheduling | Workforce assignments | Planned for future | N/A (monitoring, not inspection) | Risk-informed interval computation — dynamic, not fixed calendar |
| Condition assessment | Instrument readings + visual observations | Survey123 field forms | Monitoring types (planned) | Water level / temperature / flow | Blended score + red-flag overrides — engineering-defensible, not pure scoring |
| Field data collection | Native mobile app (offline) | Field Maps mobile app | Not yet implemented | N/A | PWA with offline-first architecture — single codebase, installable, no app store |
| Sensor/SCADA integration | Full SCADA + telemetry | Via ArcGIS integrations | Not in scope | 377 observation stations (manual) | Out of scope — registry-based data model with future sensor accommodation |
| AI / NLP capabilities | Not offered | Not offered | ANN for potential dam detection (research) | Not offered | Evidence-grounded AI copilot with citations — research assistant, not engineer |
| Candidate discovery | Not offered | Not offered | ANN-based (research phase) | Not offered | Evidence-fusion (OSM + satellite + documents) with human review — credible, debuggable |
| Multilingual support | Limited (vendor-specific) | Limited | Russian/Kazakh | Russian/Kazakh | Trilingual from architecture (RU/KK/EN) with multilingual matching |
| Standards compliance | Proprietary APIs | ArcGIS ecosystem | REST API (microservices) | Web map (proprietary) | OGC API Features/Tiles + STAC — open standards for government integration |
| Provenance tracking | Audit logs (dataset-level) | Versioned feature layers | Not offered | Not offered | Fact-level provenance via attestation model — every attribute traceable to source |
| Portfolio analytics | Configurable dashboards | ArcGIS Dashboards | Statistics collection (planned) | Basic monitoring display | Dashboard with condition distribution + repair queue + risk overview |
| Alerting | Real-time alerts/alarms | Via ArcGIS integrations | Not offered | Flood predictors module | Out of scope — not real-time monitoring; highlights critical/overdue instead |
| EAP management | EAP tracking + version control | Not core | Not offered | N/A | Out of scope — different product category |
| Deployment model | SaaS (cloud or on-prem) | ArcGIS Online/Enterprise | Self-hosted (Kubernetes) | Government-hosted | Self-hosted (FastAPI + PostGIS + MinIO) — full control, no vendor lock-in |

### Competitive Position Analysis

**Against commercial dam safety platforms (Dam360, DamData, KISTERS):**
These platforms are mature, sensor-integrated, and compliance-focused (FERC/ICOLD). They are also expensive, proprietary, and designed for large dam operators with instrumentation. Our product is for a different user: a government water resources ministry managing 1,395 mostly-instrumented-less structures with registry data, not sensor data. We compete on openness (OGC standards, no vendor lock-in), trilingual support, candidate discovery (they don't have it), and cost (open-source stack). We don't compete on real-time monitoring — that's their domain.

**Against ArcGIS Solutions:**
Esri's Dam Safety and Water Distribution solutions are comprehensive but require ArcGIS licensing and lock users into the Esri ecosystem. Kazakhstan's government is cost-conscious and increasingly favors open-source. Our MapLibre + PostGIS + TiPG stack provides equivalent map and asset management capabilities without licensing fees. We also add candidate discovery and AI copilot — neither of which ArcGIS offers natively.

**Against kazdams.kz (Kazakhstan academic project):**
This is the closest direct competitor — a Kazakhstan-specific dam monitoring GIS with dam passports, ANN-based potential dam detection, and microservices architecture (Go, PostgreSQL, Kubernetes). However, it's an academic project (funded by Ministry of Science and Higher Education, IRN AP19675038) focused on dams specifically, not the broader hydraulic infrastructure portfolio (canals, hydrological stations, water management facilities). Our product covers the full hydraulic infrastructure portfolio, adds the evidence-fusion discovery approach, trilingual support, AI copilot, and OGC standards compliance. We should monitor kazdams.kz development and potentially position as complementary (different scope) rather than competitive.

**Against Kazhydromet interactive map:**
Kazhydromet's map (ecodata.kz) shows hydrological monitoring data (377 stations, water levels, flood predictors). It's a monitoring tool, not an asset management tool. Our product is complementary — we manage the structures (canals, dams, hydraulic facilities) while Kazhydromet monitors the water. Integration via OGC APIs is a natural future step. Our product should reference Kazhydromet data as a provenance source for hydrological context.

## Sources

### Dam Safety Management Systems
- Dam360 / ADASA — dam safety management software (adasasystems.com)
- DamData / OFITECO — dam safety data management (ofiteco.com)
- DamWatch / USEngineering Solutions — dam monitoring software (usengineeringsolutions.com)
- Sysdam — dam safety risk management software (sysdam.com.br)
- KISTERS WISKI / FieldVisits — dam safety monitoring (kisters.net)
- Oxmaint — FERC Part 12 dam safety inspection CMMS (oxmaint.com)

### Water Utility Asset Management
- AquaTwin Asset / Aquanuity — AI-powered water asset management (aquanuity.com)
- Autodesk InfoAsset Manager — water network asset management (autodesk.com)
- AssetLab Canada — water/wastewater CMMS (assetlab.ca)
- GISWater / Kartoza — open-source water infrastructure GIS (kartoza.com)
- 1Spatial 1Water — enterprise water network management (1spatial.com)
- ArcGIS Solutions — Dam Safety, Water Distribution Data Management (doc.arcgis.com)

### Kazakhstan Context
- Kazhydromet interactive hydrological monitoring map (kazhydromet.kz, published 2024-08-22)
- Kazakhstan Prime Minister press releases on flood prevention and water sector modernization (primeminister.kz, 2024-2026)
- kazdams.kz — GIS for dam monitoring in Kazakhstan (jstage.jst.go.jp, IRN AP19675038)
- World Bank assessment of Kazakhstan hazard monitoring capacity (documents1.worldbank.org)
- East Kazakhstan flood hazard monitoring with Sentinel-1/2 (MDPI Applied Sciences, 2025)

### Risk-Informed Inspection Models
- World Bank Technical Note: Portfolio Risk Assessment Using Risk Index (documents1.worldbank.org)
- FEMA Federal Guidelines for Dam Safety Risk Management (P1025) (damsafety.org)
- FERC RIDM Guidelines Chapter 3 — Risk Assessment (ferc.gov)
- FERC Engineering Guidelines Chapter 18 — Level 2 Risk Analysis / SQRA (hydro.org)
- USBR Best Practices Chapter A-4 — Semi-Quantitative Risk Analysis (usbr.gov)

### AI Copilot / Industrial Asset Intelligence
- Nlyte Operational AI — infrastructure copilot with grounded insights (nlyte.com)
- Qarion AI Copilot — data catalog copilot with MCP tools and citations (qarion.com)
- IBM IndustryAssetEQA — neurosymbolic EQA for industrial assets (ACL 2026, aclanthology.org)
- IBM AssetOpsBench — AI agent framework for industrial O&M (github.com/kmn01/AssetOpsBench)
- Knowledge Graphs as Missing Data Layer for LLM Industrial Operations (arxiv.org, 2026)

### OGC Standards
- OGC API — Features (ogcapi.ogc.org/features)
- OGC API — Tiles (ogcapi.ogc.org/tiles)
- TiPG — OGC Features and Tiles API for PostGIS (developmentseed/tipg, pypi.org)
- GeoFastMap API — OGC-compliant geo API (github.com/rupestre-campos/geofastmapAPI)
- OGC Vector Tiles Pilot Phase 2 (ogc.org/initiatives/vtp2)

### STAC / Earth Observation
- STAC Specification (radiantearth/stac-spec, stacspec.org)
- OGC STAC Community Standard 25-004 v1.1.0 (ogc.org/standards/stac)
- NASA Earthdata STAC recommendations (earthdata.nasa.gov)
- USGS Landsat STAC API (usgs.gov)

### Satellite / OSM Infrastructure Detection
- GeoAI4Water / HeiGIT — water infrastructure mapping from satellite imagery (heigit.org)
- IGraSS — canal network mapping from satellite imagery (IJCAI 2025, arxiv.org)
- WWTP detection with OSM + remote sensing (PubMed, 2022)
- Critical infrastructure detection from satellite imagery — electrical substations (IOPscience, 2024)
- Water leak detection via satellite + deep learning (Springer, 2025)

### Provenance Tracking
- W3C PROV for geospatial provenance at dataset/feature/attribute levels (UAB, 2017)
- GeoPROV — minimal semantic provenance framework (Semantic Web Journal, 2025)
- Enterprise Spatial Data Provenance Knowledge Infrastructure (MDPI ISPRS Int. J. Geo-Inf., 2026)
- World Historical Gazetteer attestation model (docs.whgazetteer.org)

### PWA Offline Field Collection
- Offline-first PWA patterns for field inspection (terminalskills.io, 2026)
- CivicPlus Mobile Offline Inspection PWA (civicplus.help, 2025)
- Utility field service PWA offline operations (celestialinfosoft.com, 2025)
- Offline-first field operations sync status contract (paneo.tech)
- Offline-first waste audit field platform (GrowXLabs, 2026)
- InspectSync offline-first inspection platform (github.com/Shonu72/InspectSync-Offline-First)

---
*Feature research for: Geospatial hydraulic infrastructure / dam safety / water asset management portal*
*Researched: 2026-06-25*
