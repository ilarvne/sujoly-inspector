---
phase: 01-app-shell-i18n
plan: "02"
subsystem: ui
tags: [next-intl, i18n, routing, middleware, tailwind, oklch, design-tokens, fonts, trilingual]

# Dependency graph
requires:
  - phase: 01-app-shell-i18n/01
    provides: "Next.js 16 app scaffold with next-intl plugin, shadcn/ui, Vitest+Playwright test infrastructure"
provides:
  - "next-intl routing (routing.ts, navigation.ts, request.ts) with ru/kk/en locales, defaultLocale ru"
  - "next-intl middleware for locale detection and URL routing"
  - "Trilingual message files (en/ru/kk) with common.appTitle, nav, and 7 page namespaces"
  - "Locale layout with Inter+Manrope fonts (cyrillic + cyrillic-ext subsets), NextIntlClientProvider, globals.css import"
  - "Design system globals.css with OKLCH primary (#0b4f6c), 6 status colors, font mappings"
affects: [01-03, 01-04, 02-map-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [next-intl defineRouting/createNavigation API, dynamic locale layout with [locale] segment, OKLCH design tokens in @theme, Inter+Manrope dual-font system with CSS variables]

key-files:
  created:
    - apps/web/i18n/routing.ts
    - apps/web/i18n/navigation.ts
    - apps/web/middleware.ts
    - apps/web/messages/en.json
    - apps/web/messages/ru.json
    - apps/web/messages/kk.json
    - apps/web/app/[locale]/layout.tsx
    - apps/web/app/[locale]/not-found.tsx
    - apps/web/app/not-found.tsx
  modified:
    - apps/web/i18n/request.ts (overwritten from Wave 0 placeholder)
    - apps/web/app/globals.css (replaced shadcn defaults with project design system)
  deleted:
    - apps/web/app/layout.tsx (replaced by app/[locale]/layout.tsx)
    - apps/web/app/page.tsx (replaced by app/[locale]/page.tsx in plan 01-12)

key-decisions:
  - "Overwrote Wave 0 i18n/request.ts placeholder with full getRequestConfig using hasLocale validation and dynamic message loading"
  - "Applied B1 fix: app/[locale]/layout.tsx imports ../globals.css as first line — root layout requires CSS import"
  - "Applied B3 fix: kk.json home.subtitle contains жаһандық (һ U+04BB) to provide all 9 Kazakh-specific characters"
  - "Applied W6 fix: common.appTitle added to all 3 message files for localized app header title"
  - "Used both cyrillic AND cyrillic-ext subsets for Inter and Manrope fonts — not just cyrillic-ext"

patterns-established:
  - "Pattern 1: i18n routing via defineRouting with locales ordered ru/kk/en (defaultLocale ru)"
  - "Pattern 2: Locale layout in app/[locale]/layout.tsx with setRequestLocale + NextIntlClientProvider"
  - "Pattern 3: Design tokens in globals.css using OKLCH color space with @theme inline for shadcn semantic tokens"
  - "Pattern 4: Dual-font system — Inter (body, --font-sans) + Manrope (headings, --font-display) via next/font/google"
  - "Pattern 5: Status color tokens as @theme custom properties (--color-status-normal through --color-status-missing)"

requirements-completed: []

# Coverage metadata
coverage:
  - id: D1
    description: "i18n routing configured — routing.ts (defineRouting ru/kk/en), navigation.ts (createNavigation), request.ts (getRequestConfig with hasLocale)"
    verification:
      - kind: other
        ref: "npm run build — compiles successfully with routing config valid"
        status: pass
    human_judgment: false
  - id: D2
    description: "next-intl middleware created for locale detection and URL routing with matcher excluding api/trpc/_next/_vercel/static"
    verification:
      - kind: other
        ref: "npm run build — build succeeds, middleware recognized as Proxy (Middleware)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Trilingual message files (en/ru/kk) with common.appTitle, nav (7 items), and 7 page namespaces — all 9 Kazakh-specific Cyrillic characters present in kk.json including һ (U+04BB) in жаһандық"
    verification:
      - kind: other
        ref: "node char check — all 9 Kazakh chars (ә ғ қ ң ө ұ ү һ і) verified present in kk.json"
        status: pass
      - kind: other
        ref: "npm run build — messages resolve at build time"
        status: pass
    human_judgment: false
  - id: D4
    description: "Locale layout with Inter+Manrope fonts (cyrillic + cyrillic-ext subsets), NextIntlClientProvider, globals.css import (B1 fix), generateStaticParams for 3 locales, setRequestLocale before rendering"
    verification:
      - kind: other
        ref: "npm run build — static pages generated, no TypeScript errors"
        status: pass
      - kind: other
        ref: "First line of app/[locale]/layout.tsx verified as import '../globals.css' (B1 fix)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Design system globals.css with OKLCH primary (oklch(0.42 0.08 230) ~#0b4f6c), 6 status color tokens, --font-sans (Inter) and --font-display (Manrope) mappings, @layer base font assignments"
    verification:
      - kind: unit
        ref: "tests/design-tokens.test.ts — 6/6 tests pass (tailwindcss import, tw-animate-css import, OKLCH primary, font-sans, font-display, 6 status colors)"
        status: pass
    human_judgment: false

# Metrics
duration: 4min
completed: 2026-06-25
status: complete
---

# Phase 1 Plan 02: Waves 1+2 — i18n Foundation & Design System Summary

**next-intl routing, middleware, trilingual messages (ru/kk/en with all 9 Kazakh chars), locale layout with Inter+Manrope cyrillic fonts, and OKLCH design system with 6 status colors**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-25T21:24:47Z
- **Completed:** 2026-06-25T21:29:24Z
- **Tasks:** 5
- **Files modified:** 13 (11 created/modified, 2 deleted)

## Accomplishments
- i18n routing foundation: defineRouting (ru/kk/en, defaultLocale ru), createNavigation, getRequestConfig with hasLocale validation and dynamic message loading
- next-intl middleware created for automatic locale detection and URL routing with proper matcher exclusions
- Trilingual message files (en/ru/kk) with common.appTitle, nav (7 items), and 7 page namespaces — kk.json includes all 9 Kazakh-specific Cyrillic characters including һ (U+04BB) in "жаһандық"
- Locale layout with Inter+Manrope fonts (both cyrillic AND cyrillic-ext subsets), NextIntlClientProvider, globals.css import (B1 fix), setRequestLocale, generateStaticParams for 3 locales
- Design system globals.css configured with OKLCH primary color (~#0b4f6c governmental teal-blue), 6 status color tokens (normal/inspection/repair/critical/unknown/missing), and Inter/Manrope font variable mappings — all 6 design-tokens.test.ts assertions now pass

## Task Commits

Each task was committed atomically:

1. **Task 01-05: Create i18n Routing Files** — `6f347f7` (feat)
2. **Task 01-06: Create middleware.ts** — `7a9e319` (feat)
3. **Task 01-07: Create Message Files (en, ru, kk)** — `07f0ce7` (feat)
4. **Task 01-08: Create Locale Layout with Fonts + Providers** — `ad08af9` (feat)
5. **Task 01-09: Configure globals.css @theme** — `55eecde` (feat)

## Files Created/Modified
- `apps/web/i18n/routing.ts` — defineRouting with locales ['ru', 'kk', 'en'], defaultLocale 'ru'
- `apps/web/i18n/navigation.ts` — createNavigation(routing) exporting Link, redirect, usePathname, useRouter, getPathname
- `apps/web/i18n/request.ts` — getRequestConfig with hasLocale validation and dynamic message import (overwrote Wave 0 placeholder)
- `apps/web/middleware.ts` — createMiddleware(routing) with matcher excluding api/trpc/_next/_vercel/static
- `apps/web/messages/en.json` — English translations: common.appTitle, nav (7 items), 7 page namespaces
- `apps/web/messages/ru.json` — Russian translations: common.appTitle (Жамбыл ГТС), nav, 7 page namespaces
- `apps/web/messages/kk.json` — Kazakh translations: common.appTitle (Жамбыл СҚ), nav, 7 page namespaces, all 9 Kazakh chars present
- `apps/web/app/[locale]/layout.tsx` — Root locale layout with globals.css import, Inter+Manrope fonts, NextIntlClientProvider, setRequestLocale, generateStaticParams
- `apps/web/app/[locale]/not-found.tsx` — Locale-specific 404 page
- `apps/web/app/not-found.tsx` — Global 404 page
- `apps/web/app/globals.css` — Design system: OKLCH primary, 6 status colors, font mappings, @layer base (replaced shadcn defaults)

## Decisions Made
- Overwrote Wave 0 i18n/request.ts placeholder with full getRequestConfig — the placeholder returned hardcoded locale 'en' with empty messages; the full version uses hasLocale validation and dynamic message loading from messages/{locale}.json
- Applied all 3 critical fixes from the plan: B1 (globals.css import in layout), B3 (жаһандық in kk.json for һ char), W6 (common.appTitle in all 3 message files)
- Used both 'cyrillic' AND 'cyrillic-ext' subsets for Inter and Manrope fonts — the plan explicitly requires both, not just cyrillic-ext
- Removed @import "shadcn/tailwind.css" from globals.css — the plan's design system uses only @import "tailwindcss" and @import "tw-animate-css"; shadcn components use CSS variables which are defined in the new :root and @theme inline blocks

## Deviations from Plan

None - plan executed exactly as written. All 3 critical fixes (B1, B3, W6) were applied as specified in the plan. The Next.js 16 deprecation warning for middleware.ts (renamed to "proxy" in Next.js 16) is non-blocking — next-intl's createMiddleware still works with the middleware.ts convention and the build succeeds.

## Issues Encountered
- Next.js 16 emits a deprecation warning: "The 'middleware' file convention is deprecated. Please use 'proxy' instead." This is non-blocking — the middleware.ts convention still works, next-intl uses it, and the build succeeds. The plan specifies middleware.ts which is the correct convention for next-intl integration.

## Known Stubs
- `apps/web/app/[locale]/page.tsx` — Not yet created. The home page for locale routes will be implemented in plan 01-12. Without it, locale routes (/ru, /kk, /en) return 404. This is expected — the layout and routing infrastructure are complete, and the page content is deferred to a subsequent plan.

## Next Phase Readiness
- i18n routing, middleware, and message files are complete — ready for page components that use useTranslations()
- Locale layout with fonts and providers is complete — ready for page content
- Design system tokens are configured — ready for shadcn/ui component styling and MapLibre integration
- Ready for Plan 01-03 (next plan in Phase 1)

## Self-Check: PASSED

- All 11 key files verified present on disk (routing.ts, navigation.ts, request.ts, middleware.ts, en.json, ru.json, kk.json, [locale]/layout.tsx, [locale]/not-found.tsx, not-found.tsx, globals.css)
- Both deleted files confirmed gone (app/layout.tsx, app/page.tsx)
- All 5 task commits verified in git log (6f347f7, 7a9e319, 07f0ce7, ad08af9, 55eecde)
- Build verification: npm run build succeeds
- Design tokens verification: npx vitest run tests/design-tokens.test.ts — 6/6 pass
- Kazakh char verification: all 9 chars (ә ғ қ ң ө ұ ү һ і) present in kk.json
- B1 fix verification: first line of app/[locale]/layout.tsx is "import '../globals.css';"
- B3 fix verification: жаһандық (һ U+04BB) present in kk.json home.subtitle

---
*Phase: 01-app-shell-i18n*
*Completed: 2026-06-25*
