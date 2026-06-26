---
phase: 03-inspection-risk-ui
plan: 01
subsystem: ui
tags: [react, typescript, zustand, tanstack-query, shadcn, i18n, next-intl, tailwind]

requires:
  - phase: 02-map-dashboard-passport
    provides: MapLibre map, dashboard with Recharts, digital passport Sheet, filter panel, existing shadcn components
provides:
  - Phase 3 npm packages (react-hook-form, zod, @hookform/resolvers, papaparse, jspdf, jspdf-autotable, date-fns)
  - 13 shadcn/ui components (dialog, tabs, table, tooltip, alert, textarea, label, input, progress, accordion, dropdown-menu, avatar, scroll-area)
  - TypeScript types for InspectionRecord, DocumentMeta, RiskScore, EngineerOverride, UserRole, AuthUser
  - Mock data functions for inspections, documents, risk scores, overrides
  - TanStack Query hooks (useInspections, useDocuments, useRiskScore, useOverrides)
  - Zustand auth store with persist middleware and 4 RBAC roles
  - 7 trilingual i18n namespaces (inspection, documents, risk, auth, exportNs, override, passportTabs)
  - Unit tests for Phase 3 mock data and auth store (26 tests)
affects: [03-02, 03-03, 03-04, 03-05]

tech-stack:
  added: [react-hook-form@7.80.0, zod@4.4.3, @hookform/resolvers@5.4.0, papaparse@5.5.4, jspdf@4.2.1, jspdf-autotable@5.0.8, date-fns@4.4.0, @types/papaparse@5.5.2]
  patterns: [Zustand persist middleware for auth state, TanStack Query hooks for Phase 3 data, seeded mock data generation]

key-files:
  created:
    - apps/web/lib/stores/auth-store.ts
    - apps/web/tests/phase3-mocks.test.ts
    - apps/web/components/ui/dialog.tsx
    - apps/web/components/ui/tabs.tsx
    - apps/web/components/ui/table.tsx
    - apps/web/components/ui/tooltip.tsx
    - apps/web/components/ui/alert.tsx
    - apps/web/components/ui/textarea.tsx
    - apps/web/components/ui/label.tsx
    - apps/web/components/ui/input.tsx
    - apps/web/components/ui/progress.tsx
    - apps/web/components/ui/accordion.tsx
    - apps/web/components/ui/dropdown-menu.tsx
    - apps/web/components/ui/avatar.tsx
    - apps/web/components/ui/scroll-area.tsx
  modified:
    - apps/web/package.json
    - apps/web/lib/api/types.ts
    - apps/web/lib/api/mock-data.ts
    - apps/web/lib/api/client.ts
    - apps/web/messages/en.json
    - apps/web/messages/ru.json
    - apps/web/messages/kk.json

key-decisions:
  - "Used Zustand persist middleware for mock auth — intentionally insecure for MVP, real auth will use JWT/OAuth from backend"
  - "Auth store persists to localStorage key 'sujoly-auth' with 4 roles (admin, engineer, inspector, viewer)"
  - "Risk score uses weighted sum of 4 components (structural 35%, hydrological 25%, operational 25%, age 15%)"
  - "Mock data uses deterministic seed from structureId for reproducible test data"

patterns-established:
  - "Zustand persist pattern: create<T>()(persist((set, get) => ({...}), { name: 'store-key' }))"
  - "TanStack Query hook pattern: useQuery with enabled flag for nullable structureId, 100ms delay for mock realism"
  - "Seeded mock data: parseInt(structureId.replace(/\\D/g, '')) || 1 for deterministic generation"

requirements-completed: [DATA-05-FE, DATA-06-FE, RISK-06-FE, RISK-07-FE, RISK-08-FE]

coverage:
  - id: D1
    description: "Phase 3 npm packages installed with pinned versions (react-hook-form, zod, @hookform/resolvers, papaparse, jspdf, jspdf-autotable, date-fns)"
    requirement: "DATA-05-FE"
    verification:
      - kind: other
        ref: "npm ls react-hook-form zod @hookform/resolvers papaparse jspdf jspdf-autotable date-fns"
        status: pass
    human_judgment: false
  - id: D2
    description: "13 shadcn/ui components installed (dialog, tabs, table, tooltip, alert, textarea, label, input, progress, accordion, dropdown-menu, avatar, scroll-area)"
    requirement: "DATA-05-FE"
    verification:
      - kind: other
        ref: "Test-Path for all 13 component files — all True"
        status: pass
    human_judgment: false
  - id: D3
    description: "TypeScript types for InspectionRecord, DocumentMeta, RiskScore, EngineerOverride, UserRole, AuthUser defined in lib/api/types.ts"
    requirement: "DATA-05-FE"
    verification:
      - kind: unit
        ref: "tests/phase3-mocks.test.ts#mockInspections each record has required fields"
        status: pass
    human_judgment: false
  - id: D4
    description: "Mock data functions for inspections, documents, risk scores, overrides in lib/api/mock-data.ts"
    requirement: "DATA-06-FE"
    verification:
      - kind: unit
        ref: "tests/phase3-mocks.test.ts#mockInspections, #mockDocuments, #mockRiskScore, #mockOverrides, #mockAddDocument, #mockAddOverride"
        status: pass
    human_judgment: false
  - id: D5
    description: "TanStack Query hooks (useInspections, useDocuments, useRiskScore, useOverrides) in lib/api/client.ts"
    requirement: "DATA-06-FE"
    verification:
      - kind: other
        ref: "npm run build — TypeScript compilation passes with all hooks"
        status: pass
    human_judgment: false
  - id: D6
    description: "Zustand auth store with persist middleware and 4 RBAC roles (admin, engineer, inspector, viewer)"
    requirement: "RISK-06-FE"
    verification:
      - kind: unit
        ref: "tests/phase3-mocks.test.ts#useAuthStore — login, logout, hasRole tests"
        status: pass
    human_judgment: false
  - id: D7
    description: "7 trilingual i18n namespaces added to all 3 message files (inspection, documents, risk, auth, exportNs, override, passportTabs)"
    requirement: "RISK-07-FE"
    verification:
      - kind: other
        ref: "npm run build — static page generation for all 3 locales passes"
        status: pass
    human_judgment: false
  - id: D8
    description: "Unit tests for Phase 3 mock data and auth store (26 tests covering all new functions and store operations)"
    requirement: "RISK-08-FE"
    verification:
      - kind: unit
        ref: "tests/phase3-mocks.test.ts — 26 tests, all pass"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-06-26
status: complete
---

# Phase 3 Plan 01: Inspection & Risk UI Foundation Summary

**Data layer infrastructure for Phase 3 — 7 npm packages, 13 shadcn/ui components, 8 TypeScript types, 6 mock data functions, 4 TanStack Query hooks, Zustand auth store with RBAC, and 7 trilingual i18n namespaces**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-26
- **Completed:** 2026-06-26
- **Tasks:** 4
- **Files modified:** 20 (7 modified, 15 created)

## Accomplishments
- Installed 7 Phase 3 npm packages with pinned versions plus @types/papaparse dev dependency
- Installed 13 shadcn/ui components (dialog, tabs, table, tooltip, alert, textarea, label, input, progress, accordion, dropdown-menu, avatar, scroll-area)
- Extended types.ts with 8 new types (UserRole, AuthUser, InspectionRecord, DocumentMeta, RiskComponent, RiskScore, OverrideField, EngineerOverride)
- Created 6 mock data functions (mockInspections, mockDocuments, mockAddDocument, mockRiskScore, mockOverrides, mockAddOverride) with deterministic seeded generation
- Added 4 TanStack Query hooks (useInspections, useDocuments, useRiskScore, useOverrides) with enabled flags and 100ms delay
- Created Zustand auth store with persist middleware, 4 RBAC roles, login/logout/hasRole methods
- Added 7 trilingual i18n namespaces (inspection, documents, risk, auth, exportNs, override, passportTabs) to all 3 message files
- Wrote 26 unit tests covering all mock data functions and auth store operations — all pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Phase 3 packages and shadcn/ui components** - `6ab4b15` (feat)
2. **Task 2: Add Phase 3 types, mock data, auth store, and API hooks** - `c855599` (feat)
3. **Task 3: Add Phase 3 i18n keys to all 3 message files** - `d52c31e` (feat)
4. **Task 4: Unit tests for Phase 3 mock data and auth store** - `cd41799` (test)

## Files Created/Modified
- `apps/web/package.json` - Added 7 runtime deps + 1 dev dep
- `apps/web/lib/api/types.ts` - 8 new type definitions for Phase 3 domain
- `apps/web/lib/api/mock-data.ts` - 6 new mock data functions with seeded generation
- `apps/web/lib/api/client.ts` - 4 new TanStack Query hooks
- `apps/web/lib/stores/auth-store.ts` - Zustand auth store with persist and RBAC
- `apps/web/messages/en.json` - 7 new English i18n namespaces
- `apps/web/messages/ru.json` - 7 new Russian i18n namespaces
- `apps/web/messages/kk.json` - 7 new Kazakh i18n namespaces with Kazakh-specific chars
- `apps/web/tests/phase3-mocks.test.ts` - 26 unit tests for Phase 3 data layer
- `apps/web/components/ui/*.tsx` - 13 new shadcn/ui component files

## Decisions Made
- Used Zustand persist middleware for mock auth — intentionally insecure for MVP, real auth will use JWT/OAuth from backend
- Risk score uses weighted sum of 4 components (structural 35%, hydrological 25%, operational 25%, age 15%)
- Mock data uses deterministic seed from structureId for reproducible test data across runs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 3 infrastructure is in place: types, mock data, API hooks, auth store, i18n keys, shadcn components
- Plans 02-05 can build feature UIs on top of this foundation
- Build passes (24 static pages generated across 3 locales)
- All 69 unit tests pass (26 new Phase 3 + 43 existing Phase 1-2)

---
*Phase: 03-inspection-risk-ui*
*Completed: 2026-06-26*
