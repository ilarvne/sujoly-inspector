---
phase: 03-inspection-risk-ui
plan: 05
subsystem: ui
tags: [csv, geojson, pdf, jspdf, papaparse, export, next.js, react, playwright]

requires:
  - phase: 03-01
    provides: "exportNs i18n namespace, mock data, TanStack Query hooks, shadcn/ui components"
provides:
  - "Pure export utility functions (generateCSV, generateGeoJSON, generatePDF, downloadBlob, formatFileSize)"
  - "ExportPanel client component with CSV, GeoJSON, PDF format cards"
  - "Reports page at /[locale]/reports rendering ExportPanel"
  - "Unit tests for export utilities (10 tests)"
  - "E2E tests for export panel (5 tests)"
affects: [03-inspection-risk-ui, reports, export]

tech-stack:
  added: []
  patterns:
    - "Pure export utility functions unit-testable in jsdom (CSV/GeoJSON string generation)"
    - "Browser-only functions (generatePDF, downloadBlob) separated from pure functions"
    - "BOM prefix on CSV for Cyrillic Excel compatibility"

key-files:
  created:
    - "apps/web/lib/export/export-utils.ts"
    - "apps/web/components/export/export-panel.tsx"
    - "apps/web/tests/export-utils.test.ts"
    - "apps/web/tests/export.spec.ts"
  modified:
    - "apps/web/app/[locale]/reports/page.tsx"

key-decisions:
  - "Removed unused useLocale import from ExportPanel to avoid ESLint no-unused-vars error"
  - "Used data-slot='select-trigger' selector in E2E test instead of getByRole('combobox') to disambiguate from language switcher"
  - "Created minimal risk-score-display.tsx stub to unblock build (pre-existing missing import in passport-panel.tsx from Phase 2)"

patterns-established:
  - "Export utilities are pure functions where possible; browser-only functions (PDF, download) are clearly separated"
  - "CSV export includes BOM prefix (\\uFEFF) for Cyrillic Excel compatibility"

requirements-completed: [RISK-08-FE]

coverage:
  - id: D1
    description: "Export utility functions: generateCSV with BOM, generateGeoJSON, generatePDF, downloadBlob, formatFileSize"
    requirement: "RISK-08-FE"
    verification:
      - kind: unit
        ref: "tests/export-utils.test.ts#generateCSV produces CSV string with BOM prefix"
        status: pass
      - kind: unit
        ref: "tests/export-utils.test.ts#generateGeoJSON produces valid JSON string"
        status: pass
      - kind: unit
        ref: "tests/export-utils.test.ts#formatFileSize formats bytes correctly"
        status: pass
    human_judgment: false
  - id: D2
    description: "ExportPanel with 3 format cards (CSV, GeoJSON, PDF), structure selection for PDF, download buttons"
    requirement: "RISK-08-FE"
    verification:
      - kind: e2e
        ref: "tests/export.spec.ts#Reports page renders export panel"
        status: pass
      - kind: e2e
        ref: "tests/export.spec.ts#PDF export button disabled until structure selected"
        status: pass
      - kind: e2e
        ref: "tests/export.spec.ts#CSV export triggers download"
        status: pass
      - kind: e2e
        ref: "tests/export.spec.ts#GeoJSON export triggers download"
        status: pass
      - kind: e2e
        ref: "tests/export.spec.ts#Reports page works in English"
        status: pass
    human_judgment: false
  - id: D3
    description: "Reports page at /[locale]/reports renders ExportPanel in all 3 locales (RU/KK/EN)"
    requirement: "RISK-08-FE"
    verification:
      - kind: e2e
        ref: "tests/routes.spec.ts#ru/reports returns 200"
        status: pass
      - kind: e2e
        ref: "tests/routes.spec.ts#kk/reports returns 200"
        status: pass
      - kind: e2e
        ref: "tests/routes.spec.ts#en/reports returns 200"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-06-26
status: complete
---

# Phase 03 Plan 05: Export Panel Summary

**CSV/GeoJSON/PDF export panel at /reports with PapaParse, jsPDF, and jspdf-autotable, fully trilingual with unit and E2E tests**

## Performance

- **Duration:** 25 min
- **Tasks:** 3
- **Files modified:** 6 (4 created, 1 modified, 1 stub fix)

## Accomplishments
- Pure export utility functions with BOM-prefixed CSV (Cyrillic Excel compatible), pretty-printed GeoJSON, and jsPDF + autotable PDF generation
- ExportPanel client component with CSV/GeoJSON format cards and PDF inspection report with structure selection dropdown
- Reports page replaced from Phase 1 stub to full export panel using exportNs i18n namespace in all 3 locales
- 10 unit tests (generateCSV, generateGeoJSON, formatFileSize) and 5 E2E tests (panel rendering, PDF disabled state, CSV/GeoJSON downloads, English locale) all passing

## Task Commits

1. **Task 1: Export utility functions and unit tests** - `9352f7f` (feat)
2. **Task 2: Export panel and reports page** - `0491917` (feat)
3. **Task 3: E2E tests for export functionality** - `312edb0` (test)

**Additional commits:**
- `b54d6aa` (fix) - risk-score-display stub + commit untracked inspection-timeline to unblock build
- `8f9b421` (fix) - E2E test locator fix for combobox ambiguity

## Files Created/Modified
- `apps/web/lib/export/export-utils.ts` - Pure export functions: generateCSV (PapaParse + BOM), generateGeoJSON (JSON.stringify), generatePDF (jsPDF + autotable), downloadBlob, formatFileSize
- `apps/web/components/export/export-panel.tsx` - Client component with 3 format cards, structure dropdown for PDF, filter-aware CSV/GeoJSON export
- `apps/web/app/[locale]/reports/page.tsx` - Server Component rendering ExportPanel with exportNs translations
- `apps/web/tests/export-utils.test.ts` - 10 Vitest unit tests for pure export functions
- `apps/web/tests/export.spec.ts` - 5 Playwright E2E tests for export panel
- `apps/web/components/inspection/risk-score-display.tsx` - Minimal stub to unblock pre-existing build failure (full implementation by plan 03-03)

## Decisions Made
- Removed unused `useLocale` import from ExportPanel (plan included it but `locale` variable was never used; would trigger ESLint no-unused-vars)
- Used `data-slot="select-trigger"` CSS selector in E2E test instead of `getByRole('combobox')` to disambiguate the structure dropdown from the language switcher native `<select>`
- Created minimal `risk-score-display.tsx` stub to fix pre-existing build failure (passport-panel.tsx from Phase 2 imported a non-existent module)

## Deviations from Plan

### Auto-fixed Issues

**1. [Build Blocker] Pre-existing missing module risk-score-display.tsx**
- **Found during:** Final build verification
- **Issue:** passport-panel.tsx (committed in Phase 2) imports `@/components/inspection/risk-score-display` which didn't exist; inspection-timeline.tsx existed on disk but was untracked
- **Fix:** Created minimal functional stub for risk-score-display.tsx and committed both files
- **Files modified:** apps/web/components/inspection/risk-score-display.tsx, apps/web/components/inspection/inspection-timeline.tsx
- **Verification:** Build exits with code 0
- **Committed in:** b54d6aa

**2. [Test Fix] E2E combobox locator ambiguity**
- **Found during:** Task 3 E2E test run
- **Issue:** `page.getByRole('combobox')` matched both the language switcher and the structure dropdown
- **Fix:** Changed to `page.locator('[data-slot="select-trigger"]')` which only matches Radix Select triggers
- **Files modified:** apps/web/tests/export.spec.ts
- **Verification:** All 5 E2E tests pass
- **Committed in:** 8f9b421

---

**Total deviations:** 2 auto-fixed (1 build blocker, 1 test fix)
**Impact on plan:** Both fixes necessary for build and test correctness. No scope creep.

## Issues Encountered
- Turbopack dev server cache corruption (`.next/dev/cache` SST file missing) caused E2E test failures on second run; resolved by clearing `.next` directory
- Parallel plan execution (03-02/03-03/03-04) committed changes during 03-05 execution, including a full risk-score-display implementation that superseded the stub; no conflicts detected

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Export panel fully functional at /reports in all 3 locales
- Export utilities available for reuse by other components
- All Phase 1-2 tests still pass (24/24 route tests)

---
*Phase: 03-inspection-risk-ui*
*Completed: 2026-06-26*
