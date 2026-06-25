---
workstream: frontend
created: 2026-06-25
---

# Project State

## Current Position

**Status:** In Progress
**Current Phase:** 01-app-shell-i18n
**Last Activity:** 2026-06-25
**Last Activity Description:** Completed 01-02-PLAN.md (Waves 1+2: i18n Foundation & Design System)

## Progress

**Phases Complete:** 0
**Current Plan:** 01-02 (complete) → next: 01-03

## Session Continuity

**Stopped At:** Completed 01-02-PLAN.md
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
