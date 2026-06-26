# Roadmap: SuJoly Inspector — Frontend

## Overview

Frontend workstream: Next.js PWA + MapLibre GL JS + Tailwind + shadcn/ui + OpenUI + assistant-ui. Builds the map-first UI, digital passports, risk dashboards, discovery review, offline field mode, and AI copilot chat. 6 phases, each consuming backend APIs and delivering user-facing capabilities.

## Phases

- [x] **Phase 1: App Shell & i18n** - Next.js project, trilingual (RU/KK/EN), cyrillic-ext fonts, Tailwind, shadcn/ui, design system
- [x] **Phase 2: Map UI & Digital Passport** - MapLibre map, structure markers, digital passport, portfolio dashboard, filtering — the MVP
- [ ] **Phase 3: Inspection & Risk UI** - Inspection timeline, document upload, risk display, RBAC UI, export UI
- [ ] **Phase 4: Discovery & Matching UI** - Candidate discovery view, side-by-side comparison, HITL review, confidence badges — **COMPLETE**
- [x] **Phase 5: PWA Field Mode** - Offline capture, deferred sync, voice transcription, sync status UI
- [x] **Phase 6: AI Copilot UI** - OpenUI renderer, assistant-ui chat, copilot page, tool provider integration

## Phase Details

### Phase 1: App Shell & i18n
**Goal**: Next.js project running with trilingual UI, design system, and app shell ready for feature development
**Mode:** mvp
**Depends on**: Nothing (can start in parallel with backend Phase 1)
**Requirements**: UI-01, UI-02
**Success Criteria** (what must be TRUE):
  1. Next.js 16 project with App Router, Tailwind CSS 4, shadcn/ui configured and running
  2. User can switch UI between Russian, Kazakh, and English with all interface text translated correctly
  3. Kazakh-specific Cyrillic characters (ә, ғ, қ, ң, ө, ұ, ү, h, і) render correctly using cyrillic-ext font subset
  4. Design system established: color palette (#0b4f6c primary, status colors green/yellow/orange/red/purple/gray), Inter/Manrope fonts, clean governmental style
  5. App shell with navigation: /, /dashboard, /map, /objects, /copilot, /reports, /hydrofinder routes created
**Plans**: 01-01 (complete), 01-02 (complete), 01-03 (complete), 01-04 (complete)
**UI hint**: yes

### Phase 2: Map UI & Digital Passport
**Goal**: Interactive map with clickable structures, digital passports, and portfolio dashboard — the MVP
**Mode:** mvp
**Depends on**: Backend Phase 2 (needs REST API + TiPG vector tiles)
**Requirements**: MAP-01, MAP-02, MAP-03, MAP-04, MAP-05, DATA-04
**Success Criteria** (what must be TRUE):
  1. Interactive MapLibre map shows all structures with color-coded status symbology (green=normal, yellow=inspection, orange=repair, red=critical, gray=missing coords)
  2. Click any structure → digital passport with identity, type, geometry, specs, status, provenance
  3. Portfolio dashboard: condition distribution, repair queue, inspection coverage, geographic heatmap
  4. Map and dashboard filterable by district, basin, type, condition, inspection status
**Plans**: 4 plans
Plans:
- [x] 02-01-PLAN.md — Interactive map with color-coded structures, mock data layer, Zustand stores, TanStack Query
- [x] 02-02-PLAN.md — Digital passport side panel with identity, geometry, specs, status, provenance
- [x] 02-03-PLAN.md — Portfolio dashboard with condition donut, repair queue, inspection stats, heatmap
- [x] 02-04-PLAN.md — Filter panel with district, basin, type, condition, inspection status selectors
**UI hint**: yes

### Phase 3: Inspection & Risk UI
**Goal**: Inspection history, document management, risk display, RBAC, and export UI all operational
**Mode:** mvp
**Depends on**: Backend Phase 3 (needs risk/inspection endpoints)
**Requirements**: DATA-05-FE, DATA-06-FE, RISK-06-FE, RISK-07-FE, RISK-08-FE
**Success Criteria** (what must be TRUE):
  1. Inspection history timeline per structure (date, inspector, findings, photos, condition)
  2. Document upload/download UI via MinIO presigned URLs
  3. Risk score display with component breakdown and explanation
  4. Engineer override UI for inspection intervals and repair statuses with provenance logging
  5. Login/role gating (admin, engineer, inspector, viewer) and export UI (CSV/GeoJSON/PDF) in all three languages
**Plans**: 5 plans
Plans:
- [x] 03-01-PLAN.md — Foundation: packages, shadcn components, types, mock data, auth store, API hooks, i18n
- [ ] 03-02-PLAN.md — Passport tabs + inspection timeline + risk score + engineer override dialog
- [ ] 03-03-PLAN.md — Document upload/list wired into passport Documents tab
- [ ] 03-04-PLAN.md — RBAC: login page, user menu, permission guard
- [ ] 03-05-PLAN.md — Export UI: CSV/GeoJSON/PDF on /reports page
**UI hint**: yes

### Phase 4: Discovery & Matching UI
**Goal**: Candidate discovery view with side-by-side comparison and human-in-the-loop review workflow
**Mode:** mvp
**Depends on**: Backend Phase 4 (needs discovery/matching endpoints)
**Requirements**: DISC-04, UI-03
**Success Criteria** (what must be TRUE):
  1. Candidate list view showing found objects with confidence scores and source evidence
  2. Side-by-side comparison: existing record vs candidate with evidence chips (name similarity, distance, type agreement)
  3. Review workflow: accept (add to registry), link (merge), reject (false positive) with one-click actions
  4. Confidence badges (HIGH/MEDIUM/LOW) and provenance source chips visible throughout UI
**Plans**: 2 plans (complete)
Plans:
- [x] 04-01-PLAN.md — Foundation: discovery types, mock data (20 candidates), API hooks, Zustand store, i18n (discovery namespace), reusable components (ConfidenceBadge, SourceChip, EvidenceChip)
- [x] 04-02-PLAN.md — UI: candidate list with filters/search, side-by-side comparison with evidence chips, review actions (accept/link/reject with permission guard), discovery view orchestration, hydrofinder page wiring
**UI hint**: yes
**Goal**: Installable PWA with offline capture, deferred sync, and voice transcription
**Mode:** mvp
**Depends on**: Backend Phase 3 (needs sync endpoints)
**Requirements**: FIELD-01, FIELD-02, FIELD-03, FIELD-04, FIELD-05
**Success Criteria** (what must be TRUE):
  1. PWA installable on desktop/mobile, works offline with service worker (Serwist)
  2. Offline capture: photos, voice notes (KK/RU), GPS correction, inspection forms via IndexedDB (Dexie)
  3. Deferred sync with field-level merge conflict resolution (not last-write-wins)
  4. Voice notes transcribed post-sync using Kazakh and Russian speech-to-text APIs
  5. Per-record sync status (pending/syncing/confirmed/failed) with conflict resolution UI
**Plans**: 4 plans
Plans:
- [x] 05-01-PLAN.md — PWA foundation: Serwist service worker, manifest, offline page, i18n
- [x] 05-02-PLAN.md — Offline data layer: Dexie IndexedDB, sync engine, conflict resolution, voice transcription
- [x] 05-03-PLAN.md — Field capture UI: inspection form, photos, voice notes, GPS, header indicator
- [x] 05-04-PLAN.md — Sync queue panel, conflict resolution dialog, voice transcription status, tests
**UI hint**: yes

### Phase 6: AI Copilot UI
**Goal**: AI copilot chat with OpenUI renderer, source citations, and trilingual support
**Mode:** mvp
**Depends on**: Backend Phase 5 (needs RAG agent SSE endpoint)
**Requirements**: AI-01, AI-02, AI-05
**Success Criteria** (what must be TRUE):
  1. /copilot page with assistant-ui chat interface connected to RAG agent SSE stream
  2. OpenUI renderer renders interactive cards (StructureCard, RiskBreakdownCard, charts, tables, forms) from agent output
  3. Source citations displayed as clickable references under each answer
  4. Trilingual queries supported (RU/KK/EN) — UI language matches query language
  5. Custom SuJoly components (StructureCard, RiskBreakdownCard, InspectionCard, ReportCard) registered in OpenUI library
**Plans**: 2 plans
Plans:
- [x] 06-01-PLAN.md — Foundation: copilot types, mock AI engine with trilingual intent detection, chat Zustand store with streaming simulation, i18n keys, unit tests
- [x] 06-02-PLAN.md — Chat UI components: ChatMessage, ChatInput, SuggestedPrompts, SourceCitationList, StructureCard, RiskBreakdownCard, InspectionCard, ReportCard, CopilotChat orchestrator, page integration
**UI hint**: yes

## Progress

**Execution Order:** 1 → 2 → 3 → (4, 5, 6 can parallelize after Phase 3)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. App Shell & i18n | 4/4 | Complete | 2026-06-26 |
| 2. Map UI & Digital Passport | 4/4 | Complete | 2026-06-26 |
| 3. Inspection & Risk UI | 1/5 | In Progress | - |
| 4. Discovery & Matching UI | 2/2 | Complete | 2026-06-26 |
| 5. PWA Field Mode | 4/4 | Complete | 2026-06-26 |
| 6. AI Copilot UI | 2/2 | Complete | 2026-06-26 |
