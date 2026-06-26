---
phase: 02-map-ui-digital-passport
plan: 02
subsystem: ui
tags: [shadcn, sheet, next-intl, zustand, tanstack-query, passport, trilingual, badge]

requires:
  - phase: 02-map-ui-digital-passport
    provides: MapLibre map with click handler, selection store, useStructureDetail hook, passport i18n keys, stub PassportPanel
provides:
  - Digital passport side panel (Sheet) that opens on structure click with 6 DATA-04 sections
  - Trilingual label rendering using two-translator pattern (passport namespace for headings, map namespace for enum values)
  - E2E tests for click-to-open, provenance display, close-on-overlay, and English locale
affects: [02-03-PLAN, 02-04-PLAN]

tech-stack:
  added: []
  patterns: [Two-translator pattern for mixed-namespace i18n, Sheet open state bound to Zustand selection store, conditional rendering for optional technical spec fields]

key-files:
  created:
    - apps/web/tests/passport.spec.ts
  modified:
    - apps/web/components/map/passport-panel.tsx

key-decisions:
  - "Two-translator pattern: useTranslations('passport') for section headings and field labels, useTranslations('map') for enum value labels (condition.*, inspectionStatus.*, structureType.*) — matches the i18n layout from Plan 01 where map namespace owns nested enum keys"
  - "Sheet open state bound to !!selectedId from selection store — onOpenChange calls setSelectedId(null) when closed, so overlay click, Escape, and close button all clear selection"
  - "Optional technical spec fields rendered conditionally with null/undefined checks — only height, length, capacity, yearBuilt, designType, materials that exist are shown"
  - "Confidence badge uses variant='secondary' (neutral styling) while condition badge uses inline backgroundColor from STATUS_COLORS_HEX for color-coded urgency"

patterns-established:
  - "Pattern 1: Two-translator i18n — when a component needs both flat label keys and nested enum keys from different namespaces, use two useTranslations calls (t for labels, tMap for enums)"
  - "Pattern 2: Sheet-from-store — bind Sheet open/onOpenChange to a Zustand store value for decoupled open/close control from any component"

requirements-completed: [MAP-03, DATA-04]

coverage:
  - id: D1
    description: "Clicking a structure marker on the map opens a digital passport side panel (Sheet) on the right"
    requirement: MAP-03
    verification:
      - kind: e2e
        ref: "tests/passport.spec.ts#Click structure opens passport panel"
        status: pass
      - kind: e2e
        ref: "tests/passport.spec.ts#Passport works in English locale"
        status: pass
    human_judgment: false
  - id: D2
    description: "Passport displays all 6 DATA-04 sections: identity, geometry, administrative location, technical specifications, status, provenance"
    requirement: DATA-04
    verification:
      - kind: e2e
        ref: "tests/passport.spec.ts#Click structure opens passport panel (asserts identity heading)"
        status: pass
      - kind: e2e
        ref: "tests/passport.spec.ts#Passport shows provenance section"
        status: pass
    human_judgment: true
    rationale: "E2E tests confirm identity and provenance headings are visible, but full visual inspection of all 6 sections with correct field rendering requires human review"
  - id: D3
    description: "Passport closes when user clicks overlay, presses Escape, or clicks close button"
    requirement: MAP-03
    verification:
      - kind: e2e
        ref: "tests/passport.spec.ts#Passport closes on overlay click"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-06-26
status: complete
---

# Phase 2 Plan 02: Digital Passport Panel Summary

**Full shadcn Sheet-based passport panel with 6 DATA-04 sections, two-translator trilingual i18n, and E2E tests for click-to-open and close behavior**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-26T00:00:00Z
- **Completed:** 2026-06-26T00:08:00Z
- **Tasks:** 2
- **Files modified:** 2 (1 modified, 1 created)

## Accomplishments
- Replaced Plan 01 stub with full PassportPanel: shadcn Sheet opens on right side when a structure is selected via the map click handler
- 6 structured sections rendered with Separator dividers: identity (name, ID, type), geometry (coordinates), administrative location (region, district, nearest settlement), technical specifications (conditional fields), status (color-coded condition Badge + inspection status), provenance (source, confidence Badge, last verified)
- Two-translator i18n pattern: useTranslations('passport') for headings/labels, useTranslations('map') for enum value labels — keeps namespace ownership clean
- Loading state shown via tMap('loading') while useStructureDetail fetches
- 4 E2E tests: click-to-open (RU), provenance section visible, close-on-overlay, English locale — all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement PassportPanel with all DATA-04 sections** - `975b0ce` (feat)
2. **Task 2: E2E test for click structure → passport opens** - `f6c3adb` (test)

**Plan metadata:** (pending commit)

## Files Created/Modified
- `apps/web/components/map/passport-panel.tsx` - Full PassportPanel implementation replacing Plan 01 stub; Sheet with 6 sections, two-translator i18n, conditional technical specs, color-coded condition Badge
- `apps/web/tests/passport.spec.ts` - 4 Playwright E2E tests: click structure opens passport, provenance section visible, close on overlay click, English locale

## Decisions Made
- Two-translator pattern: useTranslations('passport') for section headings and field labels, useTranslations('map') for enum value labels (condition.*, inspectionStatus.*, structureType.*) — matches the i18n layout from Plan 01 where map namespace owns nested enum keys
- Sheet open state bound to !!selectedId from selection store — onOpenChange calls setSelectedId(null) when closed, so overlay click, Escape, and close button all clear selection
- Optional technical spec fields rendered conditionally with null/undefined checks — only height, length, capacity, yearBuilt, designType, materials that exist are shown
- Confidence badge uses variant='secondary' (neutral styling) while condition badge uses inline backgroundColor from STATUS_COLORS_HEX for color-coded urgency

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. Mock data is self-contained.

## Next Phase Readiness
- Digital passport panel complete — clicking any structure opens the full passport with all DATA-04 sections
- Passport closes cleanly via overlay, Escape, or close button
- Two-translator i18n pattern established for future components needing mixed-namespace labels
- Ready for Plan 02-03 (dashboard) and Plan 02-04 (filter) which can interact with the same selection store

---
*Phase: 02-map-ui-digital-passport*
*Completed: 2026-06-26*
