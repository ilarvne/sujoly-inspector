# Plan 02-03 Summary: Portfolio Dashboard

## Overview

Replaced the placeholder `/dashboard` route with a full portfolio analytics dashboard featuring four visualization components backed by mock data via TanStack Query, respecting the Zustand filter store state.

## Tasks Completed

### Task 1: Dashboard view with condition donut, repair queue, inspection stats, heatmap
- **Commit**: `8f22efe`
- Created 5 client components and replaced the dashboard server page:
  - `components/dashboard/dashboard-view.tsx` — orchestration component; fetches data via `useStructuresGeoJSON(useFilterStore())`, renders 4 Cards in a responsive 2-column grid, handles global loading/empty states
  - `components/dashboard/condition-donut.tsx` — Recharts PieChart donut with `STATUS_COLORS_HEX` cell colors, innerRadius=60 for donut effect, Tooltip + Legend
  - `components/dashboard/repair-queue.tsx` — filters for `repair` + `critical` conditions, sorted critical-first, shows structure name (locale-resolved via `useLocale`), type, district, and colored condition Badge
  - `components/dashboard/inspection-stats.tsx` — 3 stat cards: totalStructures (55), needsInspection (33), coverageRate (20%)
  - `components/dashboard/heatmap-view.tsx` — Recharts BarChart showing structure counts by district, sorted descending
  - `app/[locale]/dashboard/page.tsx` — Server Component renders title/subtitle + DashboardView client component
- **Verification**: `npm run build` passed (TypeScript + 24 static pages)

### Task 2: E2E test for dashboard rendering and data display
- **Commit**: `0cfb8a3`
- Created `tests/dashboard.spec.ts` with 6 Playwright tests:
  1. `/ru/dashboard renders dashboard title` — h1 contains "Панель управления"
  2. `/ru/dashboard shows condition distribution chart` — section heading + Recharts SVG visible
  3. `/ru/dashboard shows repair queue` — heading visible + structure name "Тасуткель" present
  4. `/ru/dashboard shows inspection stats` — heading visible + total count "55" present
  5. `/ru/dashboard shows geographic distribution` — heading + Recharts bar chart SVG visible
  6. `/en/dashboard renders in English` — h1 contains "Dashboard" + English section headings
- **Fix during testing**: Changed `svg.recharts-surface` selector to `svg[role="application"]` because Recharts Legend renders small icon SVGs with the same class, causing strict mode violations
- **Verification**: All 6 dashboard tests + 21 route tests pass (27 total)

## Verification Results

| Check | Result |
|-------|--------|
| `npm run build` | PASS — TypeScript compiled, 24 static pages generated |
| `npx vitest run` | PASS — 43 tests (design-tokens 6, mock-data 18, types 10, stores 9) |
| `npx playwright test` (dashboard + routes) | PASS — 27 tests (6 dashboard + 21 routes) |
| `npx playwright test` (full suite) | 46 passed, 4 failed — failures are from `passport.spec.ts` (Plan 02-02 parallel work, not this plan's files) |

## Key Deliverables

- `/dashboard` route renders portfolio analytics for all 55 mock structures
- Condition distribution donut with 5 color-coded segments matching map symbology
- Repair queue listing 22 structures (11 critical + 11 repair), sorted by severity
- Inspection coverage stat cards: 55 total, 33 needing inspection, 20% coverage
- Geographic distribution bar chart by district (4 districts)
- All labels translated in 3 locales (ru, kk, en) via `useTranslations('dashboard')` and `useTranslations('map')`
- Dashboard data respects filter store state via `useFilterStore()`

## Deviations

None. All tasks executed as planned.

## Duration

~25 minutes (Task 1: ~15 min, Task 2: ~10 min including test fix)
