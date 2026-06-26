---
workstream: frontend
created: 2026-06-25
---

# Project State

## Current Position

**Status:** Phase 03 In Progress (Wave 2)
**Current Phase:** 03-inspection-risk-ui (in progress)
**Last Activity:** 2026-06-26
**Last Activity Description:** Completed 03-01-PLAN.md (Wave 1: Foundation) — packages, shadcn components, types, mock data, auth store, API hooks, i18n, unit tests

## Progress

**Phases Complete:** 2
**Current Plan:** 03-01 (complete) — Phase 3 Wave 1 foundation done, Wave 2 in progress

## Session Continuity

**Stopped At:** Completed 03-01-PLAN.md — Phase 3 Wave 1 foundation complete, Wave 2 (03-02, 03-04, 03-05) executing in parallel
**Resume File:** None

## Decisions

- Used radix-nova preset for shadcn (v4.11.0 equivalent of new-york style — CLI evolved)
- Created minimal i18n/request.ts placeholder to satisfy next-intl build requirement
- Added testMatch filter to Playwright config to exclude Vitest .test.ts files
- Overwrote Wave 0 i18n/request.ts placeholder with full getRequestConfig using hasLocale validation
- Applied B1 fix: app/[locale]/layout.tsx imports ../globals.css as first line
- Applied B3 fix: kk.json home.subtitle contains жаһандық (һ U+04BB) for all 9 Kazakh chars
- Applied W6 fix: common.appTitle added to all 3 message files
- Used both cyrillic AND cyrillic-ext subsets for Inter and Manrope fonts
- OKLCH design system: primary oklch(0.42 0.08 230) ~#0b4f6c, 6 status color tokens
- All async page components use await getTranslations() from next-intl/server — useTranslations() hook cannot run in async Server Components (B2 fix)
- AppShell header uses t('appTitle') from common namespace via getTranslations — not hardcoded string (W6 fix)
- Set fullyParallel=false in Playwright config — Turbopack dev server has race condition with concurrent page compilation
- components.json style remains 'radix-nova' (not 'new-york') — deliberate decision from 01-01, radix-nova is v4.11.0 equivalent
- Task 01-15 fix: added home.description field with Kazakh chars ә and ғ to KK messages — ensures all 9 Kazakh chars present on KK page for fonts.spec.ts
- Task 01-16 manual verification automated via Playwright browser tools — 7/8 checks fully automated, 1/8 (design aesthetic) verified programmatically with objective criteria
- Phase 1 verification gate passed: build 24 pages, Vitest 6/6, Playwright 30/30 all green
