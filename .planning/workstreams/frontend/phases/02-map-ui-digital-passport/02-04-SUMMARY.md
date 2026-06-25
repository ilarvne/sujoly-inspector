---
phase: 02-map-ui-digital-passport
plan: 04
subsystem: ui
tags: [filter, zustand, shadcn, select, i18n, map, dashboard]

requires:
  - phase: 02-map-ui-digital-passport
    plan: 01
    provides: Interactive MapLibre map, Zustand filter store, TanStack Query hooks, shadcn Select/Badge/Button components, filter i18n keys
provides:
  - FilterPanel with 5 dropdown selectors (district, basin, type, condition, inspection status) and reset button
  - Collapsible map overlay panel wired to useFilterStore
  - E2E tests verifying filter selection, reset, cross-route persistence, and trilingual rendering
affects: []

tech-stack:
  added: []
  patterns: [Two-translator pattern (filter namespace for labels, map namespace for enum options), Collapsible overlay panel with useState toggle, Sentinel value for All option in controlled Select]

key-files:
  modified:
    - apps/web/components/map/filter-panel.tsx
  created:
    - apps/web/tests/filter.spec.ts

key-decisions:
  - "Used sentinel value '__all__' for the All option in Radix Select — maps to setFilter(key, null) on change, enabling controlled Select with null store values"
  - "Two-translator pattern: useTranslations('filter') for panel labels, useTranslations('map') for enum option labels (condition.*, inspectionStatus.*, structureType.*)"
  - "Test 4 (filter persistence) uses client-side navigation via sidebar links instead of page.goto — Zustand store is a module-level singleton that survives client-side route transitions but not full page reloads"
  - "Each SelectTrigger has aria-label matching its filter label for Playwright getByRole('combobox', { name }) targeting"
  - "Filter panel includes data-testid='filter-panel' for robust test targeting"
  - "Collapse toggle uses ChevronDownIcon with rotate-180 transition — expanded points up, collapsed points down"

patterns-established:
  - "Pattern: Controlled Radix Select with null-to-sentinel mapping — value={storeValue ?? ALL_VALUE}, onValueChange converts sentinel back to null"
  - "Pattern: Collapsible overlay panel — absolute positioned with z-10, useState for collapsed state, conditional rendering of body"
  - "Pattern: Cross-route state persistence test — apply filter on /map, navigate via sidebar link to /dashboard, navigate back, verify store persisted"

requirements-completed: [MAP-05]

coverage:
  - id: F1
    description: "Filter panel renders on /map with 5 dropdown selectors and translated labels"
    requirement: MAP-05
    verification:
      - kind: e2e
        ref: "tests/filter.spec.ts#Filter panel is visible on map page"
        status: pass
      - kind: e2e
        ref: "tests/filter.spec.ts#Filter works in English locale"
        status: pass
    human_judgment: false
  - id: F2
    description: "Selecting a condition filter updates the UI (trigger text + active filter badge)"
    requirement: MAP-05
    verification:
      - kind: e2e
        ref: "tests/filter.spec.ts#Selecting condition filter updates UI"
        status: pass
    human_judgment: false
  - id: F3
    description: "Reset button clears all filters and restores All option"
    requirement: MAP-05
    verification:
      - kind: e2e
        ref: "tests/filter.spec.ts#Reset button clears filters"
        status: pass
    human_judgment: false
  - id: F4
    description: "Filter state persists across client-side route navigation (map to dashboard and back)"
    requirement: MAP-05
    verification:
      - kind: e2e
        ref: "tests/filter.spec.ts#Filter persists when navigating to dashboard and back"
        status: pass
    human_judgment: false
  - id: F5
    description: "Build passes with no TypeScript errors"
    requirement: MAP-05
    verification:
      - kind: build
        ref: "npm run build"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-06-26
status: complete
---

# Phase 2 Plan 04: Filter Panel Summary

**Filter panel with 5 dropdown selectors wired to Zustand store, providing real-time map and dashboard filtering with trilingual i18n and cross-route state persistence**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-06-26T04:13:06Z
- **Completed:** 2026-06-26T04:17:00Z
- **Tasks:** 2
- **Files modified:** 2 (1 modified, 1 created)

## Accomplishments
- FilterPanel replaces Plan 01 stub with full implementation: 5 shadcn Select dropdowns (district, basin, type, condition, inspection status) plus reset button
- Each dropdown has an 'All' option that clears that specific filter; reset button clears all filters at once
- Active filter count shown as Badge; reset button disabled when no filters active
- Panel is a collapsible overlay (absolute top-4 left-4 z-10) with ChevronDown toggle
- Two-translator pattern: useTranslations('filter') for labels, useTranslations('map') for enum options
- Filter changes update Zustand store → TanStack Query recomputes filtered GeoJSON → MapView reactively updates markers (no extra wiring needed)
- 5 E2E tests: panel visibility, filter selection, reset, cross-route persistence, English locale

## Task Commits

1. **Task 1: Implement FilterPanel with 5 dropdowns and reset button** - `26c7055` (feat)
2. **Task 2: E2E test for filter functionality on map and dashboard** - `3669a77` (test)

## Files Created/Modified
- `apps/web/components/map/filter-panel.tsx` - Full FilterPanel implementation replacing stub: 5 Select dropdowns, reset button, active filter badge, collapsible overlay
- `apps/web/tests/filter.spec.ts` - 5 Playwright E2E tests for filter panel visibility, selection, reset, persistence, and i18n

## Decisions Made
- Used sentinel value `__all__` for the All option in Radix Select — the store uses `null` for "no filter", but Radix Select requires string values. The onValueChange handler converts `__all__` back to `null` when calling `setFilter`.
- Test 4 (filter persistence) uses client-side navigation via sidebar links instead of `page.goto()`. Zustand stores are module-level singletons that persist across client-side route transitions but are re-created on full page reloads. The test navigates /map → /dashboard → /map and verifies the filter is still applied.
- Each SelectTrigger has `aria-label` set to the translated filter label, enabling `page.getByRole('combobox', { name: '...' })` targeting in Playwright tests.

## Deviations from Plan

### Adapted Approach

**1. [Rule 2 - Missing critical] Dashboard test adaptation**
- **Found during:** Task 2 (test 4 preparation)
- **Issue:** Plan specifies test 4 should verify "Dashboard charts reflect the active filter" by navigating to /dashboard and checking chart data. However, Plan 02-03 (dashboard) is executing in parallel and the dashboard page is currently a placeholder with only title/subtitle — no charts or data components exist yet.
- **Adaptation:** Test 4 verifies filter persistence by navigating to /dashboard via client-side sidebar link (confirming the page loads), then navigating back to /map via sidebar link, and verifying the filter is still applied (condition Select trigger shows the selected value, active filter badge is visible). This tests the actual persistence mechanism (Zustand store surviving client-side route navigation) without depending on the dashboard's implementation.
- **Files modified:** apps/web/tests/filter.spec.ts
- **Verification:** All 5 filter tests pass, all 40 Playwright tests pass, all 43 vitest tests pass
- **Committed in:** 3669a77 (Task 2 commit)

---

**Total deviations:** 1 (Rule 2 - missing critical dependency on parallel plan)
**Impact on plan:** Test 4 adapted to not depend on Plan 02-03's dashboard implementation. Once Plan 02-03 completes, the test can be extended to also verify dashboard chart data reflects the active filter.

## Issues Encountered
None

## User Setup Required
None

## Next Phase Readiness
- Filter panel complete — all 5 filter dimensions functional
- Filter changes reactively update map markers via Zustand → TanStack Query → react-map-gl Source
- Filter state persists across route navigation (verified by E2E test)
- Dashboard (Plan 02-03) will automatically benefit from filter store integration when complete
- All Phase 1 and Plan 02-01 tests still pass (no regressions)

---
*Phase: 02-map-ui-digital-passport*
*Completed: 2026-06-26*
