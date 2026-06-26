---
workstream: frontend
created: 2026-06-25
---

# Project State

## Current Position

**Status:** Phase 05 Complete
**Current Phase:** 05-pwa-field-mode (complete)
**Last Activity:** 2026-06-26
**Last Activity Description:** Completed Phase 5 PWA Field Mode — PWA foundation (Serwist SW, manifest, offline page), offline data layer (Dexie IndexedDB, sync engine, conflict resolution), field capture UI (inspection form, photos, voice notes, GPS), sync status UI (queue panel, conflict dialog, voice transcription status), 28 new unit tests

## Progress

**Phases Complete:** 4 (1, 2, 5, 6)
**Current Plan:** 05-04 (complete)

## Session Continuity

**Stopped At:** Phase 5 complete — all 4 plans executed, build passes (33 pages), 134/134 tests pass
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
- Phase 6: Built custom chat UI without external AI chat libraries (assistant-ui/OpenUI) — custom implementation follows existing patterns, avoids dependency risk
- Phase 6: Mock AI engine uses keyword-based intent detection with trilingual dictionaries — explain_condition and summarize_inspections checked before list_repair/list_inspection for correct precedence
- Phase 6: Chat store uses Zustand persist with partialize to strip isStreaming flags before localStorage save
- Phase 6: Source citations navigate to /map with selectedId set via selection store
- Phase 6: 4 interactive card types (StructureCard, RiskBreakdownCard, InspectionCard, ReportCard) render inline in chat messages
- Phase 5: Serwist build plugin (@serwist/next webpack) not compatible with Next.js 16 Turbopack — used manual public/sw.js with vanilla Service Worker APIs instead
- Phase 5: SerwistProvider replaced with simple useEffect-based SW registration (components/pwa/sw-register.tsx, prod only)
- Phase 5: Dexie database (sujoly-field-db) with 4 tables: fieldInspections, fieldPhotos, fieldVoiceNotes, syncQueue — all typed with EntityTable
- Phase 5: Sync engine uses mutex flag (isSyncing) to prevent concurrent sync runs on connectivity flicker
- Phase 5: Voice transcription is mock — returns randomized KK/RU text, designed for easy swap to real API
- Phase 5: Field mode store uses Zustand persist (key 'sujoly-field-mode') for field mode toggle + lastSyncAt
- Phase 5: fake-indexeddb used for Dexie unit testing in jsdom environment
- Phase 5: Conflict resolution is field-level (not last-write-wins) — detectConflicts compares 6 fields, applyResolution merges per-field
- Phase 5: Build passes 33 pages, 134 unit tests (28 new for Phase 5)
