---
phase: 01-app-shell-i18n
plan: "03"
subsystem: ui
tags: [next-intl, app-shell, sidebar, language-switcher, routing, server-components, client-components, getTranslations]

# Dependency graph
requires:
  - phase: 01-app-shell-i18n/01-02
    provides: "next-intl routing, middleware, trilingual messages, locale layout with fonts, OKLCH design system"
provides:
  - "Navigation constants (navItems with 7 routes, locales array)"
  - "App shell with sidebar (locale-aware active links) and language switcher (route-preserving)"
  - "AppShell header using localized common.appTitle via getTranslations"
  - "Home page and 6 route pages with async getTranslations (B2 fix)"
  - "AppShell wired into locale layout with globals.css import preserved (B1 fix)"
affects: [01-04, 02-map-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [async Server Component using getTranslations from next-intl/server, Client Components using useTranslations + @/i18n/navigation imports, route-preserving locale switch via router.replace(pathname, { locale })]

key-files:
  created:
    - apps/web/lib/constants.ts
    - apps/web/components/layout/app-shell.tsx
    - apps/web/components/layout/sidebar.tsx
    - apps/web/components/layout/language-switcher.tsx
    - apps/web/app/[locale]/page.tsx
    - apps/web/app/[locale]/dashboard/page.tsx
    - apps/web/app/[locale]/map/page.tsx
    - apps/web/app/[locale]/objects/page.tsx
    - apps/web/app/[locale]/copilot/page.tsx
    - apps/web/app/[locale]/reports/page.tsx
    - apps/web/app/[locale]/hydrofinder/page.tsx
  modified:
    - apps/web/app/[locale]/layout.tsx (added AppShell import and wrapper)
    - apps/web/playwright.config.ts (set fullyParallel=false for Turbopack dev server compatibility)

key-decisions:
  - "All async page components use await getTranslations() from next-intl/server — useTranslations() hook cannot run in async Server Components (B2 fix)"
  - "AppShell header uses t('appTitle') from common namespace via getTranslations — not hardcoded string (W6 fix)"
  - "Set fullyParallel=false in Playwright config — Turbopack dev server has a race condition with concurrent page compilation causing JSON.parse errors"
  - "components.json style remains 'radix-nova' (not 'new-york') — deliberate decision from plan 01-01, radix-nova is the v4.11.0 equivalent"

patterns-established:
  - "Pattern 1: Async page components use getTranslations(namespace) from next-intl/server with setRequestLocale(locale) before rendering"
  - "Pattern 2: Client Components (Sidebar, LanguageSwitcher) use 'use client' directive with useTranslations hook and @/i18n/navigation imports"
  - "Pattern 3: Navigation constants in lib/constants.ts define routes with href and labelKey for type-safe nav rendering"
  - "Pattern 4: Route-preserving locale switch via router.replace(pathname, { locale }) from @/i18n/navigation"
  - "Pattern 5: AppShell as async Server Component wraps children in locale layout — header + sidebar + main content area"

requirements-completed: []

# Coverage metadata
coverage:
  - id: D1
    description: "Navigation constants with 7 routes (home, dashboard, map, objects, copilot, reports, hydrofinder) and locales array"
    verification:
      - kind: other
        ref: "npm run build — compiles successfully with navItems and locales constants"
        status: pass
    human_judgment: false
  - id: D2
    description: "AppShell async Server Component with localized header (common.appTitle via getTranslations), Sidebar with locale-aware active links, LanguageSwitcher with route-preserving locale switch"
    verification:
      - kind: other
        ref: "npm run build — AppShell, Sidebar, LanguageSwitcher compile without errors"
        status: pass
      - kind: e2e
        ref: "tests/i18n.spec.ts#language switcher navigates from RU to KK — passes"
        status: pass
      - kind: e2e
        ref: "tests/i18n.spec.ts#language switcher navigates from KK to EN — passes"
        status: pass
    human_judgment: false
  - id: D3
    description: "Home page with async getTranslations('home') — localized title and subtitle rendered for all 3 locales"
    verification:
      - kind: e2e
        ref: "tests/i18n.spec.ts#RU locale renders Russian text — h1 contains 'Каталог'"
        status: pass
      - kind: e2e
        ref: "tests/i18n.spec.ts#KK locale renders Kazakh text — h1 contains 'каталогы'"
        status: pass
      - kind: e2e
        ref: "tests/i18n.spec.ts#EN locale renders English text — h1 contains 'Catalog'"
        status: pass
    human_judgment: false
  - id: D4
    description: "6 route pages (dashboard, map, objects, copilot, reports, hydrofinder) with async getTranslations — all 21 route-locale combinations return 200"
    verification:
      - kind: e2e
        ref: "tests/routes.spec.ts — 21/21 tests pass (7 routes x 3 locales all return 200)"
        status: pass
    human_judgment: false
  - id: D5
    description: "AppShell wired into locale layout with globals.css import preserved (B1 fix) — full app shell renders on all pages"
    verification:
      - kind: other
        ref: "npm run build — 21 static pages generated, no TypeScript errors"
        status: pass
      - kind: e2e
        ref: "tests/i18n.spec.ts#invalid locale returns 404 — passes"
        status: pass
    human_judgment: true
    rationale: "Visual layout of sidebar, header, and language switcher requires human verification of correct rendering, spacing, and active link styling"

# Metrics
duration: 8min
completed: 2026-06-26
status: complete
---

# Phase 1 Plan 03: Wave 3 — App Shell & Routes Summary

**App shell with sidebar + route-preserving language switcher, 7 localized route pages using async getTranslations, all 21 route-locale combinations verified passing**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-26T02:31:48Z
- **Completed:** 2026-06-26T02:40:13Z
- **Tasks:** 5
- **Files modified:** 13 (11 created, 2 modified)

## Accomplishments
- Navigation constants (lib/constants.ts) with 7 route definitions (href + labelKey) and locales array
- App shell components: AppShell (async Server Component with getTranslations for localized header), Sidebar (Client Component with useTranslations for nav labels and active link highlighting), LanguageSwitcher (Client Component with data-testid and route-preserving locale switch)
- Home page with async getTranslations('home') — B2 fix applied (useTranslations hook cannot run in async Server Components)
- 6 route pages (dashboard, map, objects, copilot, reports, hydrofinder) all using async getTranslations with setRequestLocale
- AppShell wired into locale layout with globals.css import preserved (B1 fix) — all 21 static pages generated successfully
- All 21 route-locale combinations verified passing (routes.spec.ts), language switching and 404 verified passing (i18n.spec.ts)

## Task Commits

Each task was committed atomically:

1. **Task 01-10: Create Navigation Constants** — `41c4ef7` (feat)
2. **Task 01-11: Create App Shell Components** — `4e890a0` (feat)
3. **Task 01-12: Create Home Page** — `39f797e` (feat)
4. **Task 01-13: Create 6 Route Pages** — `18ad529` (feat)
5. **Task 01-14: Wire AppShell into Layout** — `df7a9a2` (feat)

## Files Created/Modified
- `apps/web/lib/constants.ts` — Navigation constants: navItems (7 routes with href + labelKey), locales array
- `apps/web/components/layout/app-shell.tsx` — Async Server Component: header with localized appTitle, sidebar, main content area
- `apps/web/components/layout/sidebar.tsx` — Client Component: nav links with useTranslations('nav'), active link highlighting via usePathname
- `apps/web/components/layout/language-switcher.tsx` — Client Component: locale dropdown with data-testid, route-preserving switch via router.replace
- `apps/web/app/[locale]/page.tsx` — Home page: async getTranslations('home'), h1 title + p subtitle
- `apps/web/app/[locale]/dashboard/page.tsx` — Dashboard page: async getTranslations('dashboard')
- `apps/web/app/[locale]/map/page.tsx` — Map page: async getTranslations('map')
- `apps/web/app/[locale]/objects/page.tsx` — Objects page: async getTranslations('objects')
- `apps/web/app/[locale]/copilot/page.tsx` — Copilot page: async getTranslations('copilot')
- `apps/web/app/[locale]/reports/page.tsx` — Reports page: async getTranslations('reports')
- `apps/web/app/[locale]/hydrofinder/page.tsx` — Hydrofinder page: async getTranslations('hydrofinder')
- `apps/web/app/[locale]/layout.tsx` — Modified: added AppShell import and wrapped children with <AppShell> (B1 fix preserved)
- `apps/web/playwright.config.ts` — Modified: set fullyParallel=false to fix Turbopack dev server race condition

## Decisions Made
- All async page components use `await getTranslations()` from `next-intl/server` instead of `useTranslations()` — the hook cannot run in async Server Components (B2 fix as specified in plan)
- AppShell header uses `t('appTitle')` from `common` namespace via `getTranslations` — not hardcoded "Жамбыл ГТС" (W6 fix as specified in plan)
- Set `fullyParallel: false` in Playwright config — Turbopack dev server has a race condition when multiple Playwright workers concurrently request compilation of different dynamic route pages, causing JSON.parse errors. Production build works fine with parallelism; only the dev server (used by Playwright) is affected
- components.json style remains "radix-nova" (not "new-york" as the plan's cleanup checklist expected) — this was a deliberate decision from plan 01-01 where the shadcn CLI v4.11.0 evolved to use radix-nova as the equivalent of new-york style. Changing it would break the shadcn CLI integration

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Playwright config fullyParallel race condition**
- **Found during:** Task 01-13 (6 route pages verification)
- **Issue:** Playwright config had `fullyParallel: true` with 8 workers. When all 21 route tests ran simultaneously, the Turbopack dev server encountered concurrent compilation race conditions, producing `SyntaxError: Unexpected non-whitespace character after JSON at position 1826` errors. 14 of 21 tests returned 500 instead of 200
- **Fix:** Set `fullyParallel: false` in playwright.config.ts so tests run sequentially. All 21 tests pass with this setting. The production build (`npm run build`) is unaffected — all 21 static pages generate successfully with parallelism
- **Files modified:** apps/web/playwright.config.ts
- **Verification:** `npx playwright test tests/routes.spec.ts` — 21/21 pass. `npx playwright test tests/i18n.spec.ts` — 6/6 pass
- **Committed in:** 18ad529 (Task 01-13 commit)

**2. [Note - Pre-existing Decision] components.json style field**
- **Found during:** Task 01-14 (cleanup checklist)
- **Issue:** Plan's cleanup checklist expects `components.json` to have `"style": "new-york"`, but the actual file has `"style": "radix-nova"`. This was a deliberate decision from plan 01-01 (documented in STATE.md: "Used radix-nova preset for shadcn (v4.11.0 equivalent of new-york style — CLI evolved)")
- **Fix:** No change made — "radix-nova" is the correct value for the installed shadcn CLI version. Changing it would break the CLI integration
- **Files modified:** None
- **Verification:** components.json `tailwind.config` is `""` (correct). Style field is a pre-existing decision, not a regression

---

**Total deviations:** 1 auto-fixed (1 bug), 1 noted pre-existing decision (no change)
**Impact on plan:** The Playwright config fix was necessary for test verification to pass. The components.json note is informational — the plan's expectation didn't account for the shadcn CLI evolution documented in 01-01. No scope creep.

## Issues Encountered
- Turbopack dev server race condition with parallel Playwright workers — resolved by setting fullyParallel=false. This is a Turbopack dev server limitation, not a code issue. The production build handles all 21 pages in parallel without issues.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- App shell with sidebar and language switcher is complete and verified
- All 7 routes are accessible in all 3 locales with localized content
- Language switching preserves the current route and renders correct translations
- Ready for Plan 01-04 (next plan in Phase 1)
- Sidebar active link highlighting and language switcher dropdown styling may need visual review for design polish

## Self-Check: PASSED

- All 11 key files verified present on disk (constants.ts, app-shell.tsx, sidebar.tsx, language-switcher.tsx, 7 page files)
- Both modified files verified (layout.tsx with AppShell, playwright.config.ts with fullyParallel=false)
- All 5 task commits verified in git log (41c4ef7, 4e890a0, 39f797e, 18ad529, df7a9a2)
- Build verification: npm run build succeeds — 21 static pages generated (7 routes x 3 locales)
- routes.spec.ts: 21/21 tests pass (all route-locale combinations return 200)
- i18n.spec.ts: 6/6 tests pass (locale rendering, language switching, 404)
- B1 fix verification: first line of app/[locale]/layout.tsx is "import '../globals.css';"
- W6 fix verification: AppShell uses getTranslations('common') and t('appTitle') for header title
- B2 fix verification: all page components use await getTranslations() from next-intl/server

---
*Phase: 01-app-shell-i18n*
*Completed: 2026-06-26*
