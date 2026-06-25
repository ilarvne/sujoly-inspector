---
phase: 01-app-shell-i18n
plan: "01"
subsystem: ui
tags: [nextjs, next-intl, shadcn, vitest, playwright, tailwind, typescript]

# Dependency graph
requires: []
provides:
  - "Next.js 16 app at apps/web/ with TypeScript, Tailwind 4, App Router, Turbopack"
  - "next-intl 4.13.0 plugin configured in next.config.ts"
  - "shadcn/ui initialized with radix-nova style, neutral base color, CSS variables"
  - "Vitest + Playwright test infrastructure with TDD contract test files"
  - "Minimal i18n/request.ts placeholder for build compatibility"
affects: [01-02, 01-03, 01-04, 02-map-ui]

# Tech tracking
tech-stack:
  added: [next@16.2.9, react@19.2.4, next-intl@4.13.0, shadcn@4.11.0, vitest@3.2.4, @testing-library/react@16.3.0, @playwright/test@1.52.0, jsdom@26.1.0, lucide-react, class-variance-authority, clsx, tailwind-merge, tw-animate-css, radix-ui]
  patterns: [App Router, Tailwind v4 CSS-native @theme, shadcn/ui component system, next-intl plugin wrapping, TDD contract tests]

key-files:
  created:
    - apps/web/package.json
    - apps/web/tsconfig.json
    - apps/web/next.config.ts
    - apps/web/app/layout.tsx
    - apps/web/app/page.tsx
    - apps/web/app/globals.css
    - apps/web/postcss.config.mjs
    - apps/web/components.json
    - apps/web/lib/utils.ts
    - apps/web/components/ui/button.tsx
    - apps/web/i18n/request.ts
    - apps/web/vitest.config.ts
    - apps/web/playwright.config.ts
    - apps/web/tests/design-tokens.test.ts
    - apps/web/tests/routes.spec.ts
    - apps/web/tests/i18n.spec.ts
    - apps/web/tests/fonts.spec.ts
  modified:
    - apps/web/app/globals.css (shadcn init updated tokens)
    - apps/web/package.json (deps added)
    - apps/web/next.config.ts (next-intl plugin wrapper)

key-decisions:
  - "Used radix-nova preset for shadcn (v4.11.0 equivalent of new-york style — CLI evolved)"
  - "Created minimal i18n/request.ts placeholder to satisfy next-intl build requirement"
  - "Added testMatch filter to Playwright config to exclude Vitest .test.ts files"

patterns-established:
  - "Pattern 1: next.config.ts wraps withNextIntl(nextConfig) for i18n plugin"
  - "Pattern 2: Vitest tests in tests/*.test.ts, Playwright tests in tests/*.spec.ts"
  - "Pattern 3: shadcn/ui components in components/ui/ with cn() utility in lib/utils.ts"
  - "Pattern 4: TDD contract — test files with full assertions created before implementation"

requirements-completed: []

# Coverage metadata
coverage:
  - id: D1
    description: "Next.js 16 app scaffolded at apps/web/ with TypeScript, Tailwind 4, ESLint, App Router, Turbopack"
    verification:
      - kind: other
        ref: "npm run build — compiles successfully, generates static pages"
        status: pass
    human_judgment: false
  - id: D2
    description: "All Phase 1 dependencies installed: next-intl 4.13.0, shadcn/ui (radix-nova), Vitest 3.2.4, Playwright 1.52.0"
    verification:
      - kind: other
        ref: "npm run build succeeds with all deps; package.json verified"
        status: pass
    human_judgment: false
  - id: D3
    description: "next.config.ts wrapped with createNextIntlPlugin() for i18n"
    verification:
      - kind: other
        ref: "npm run build succeeds with next-intl plugin active"
        status: pass
    human_judgment: false
  - id: D4
    description: "Test infrastructure: Vitest config, Playwright config, 4 TDD contract test files (36 total test cases)"
    verification:
      - kind: unit
        ref: "tests/design-tokens.test.ts#design tokens in globals.css — 4 pass, 2 fail (expected TDD)"
        status: pass
      - kind: other
        ref: "npx vitest run loads config and runs tests successfully"
        status: pass
    human_judgment: false

# Metrics
duration: 12min
completed: 2026-06-25
status: complete
---

# Phase 1 Plan 01: Wave 0 — Scaffolding & Test Infrastructure Summary

**Next.js 16 app scaffolded with next-intl plugin, shadcn/ui (radix-nova), and Vitest+Playwright TDD contract test suite (36 test cases across 4 files)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-25T21:07:59Z
- **Completed:** 2026-06-25T21:20:56Z
- **Tasks:** 4
- **Files modified:** 29

## Accomplishments
- Next.js 16.2.9 app scaffolded at apps/web/ with TypeScript, Tailwind CSS 4, ESLint, App Router, Turbopack — build passes
- next-intl@4.13.0 installed and plugin configured in next.config.ts with minimal i18n/request.ts placeholder
- shadcn/ui initialized with radix-nova style (v4.11.0 equivalent of new-york), neutral base color, CSS variables — components.json has config="" for Tailwind v4
- Full test infrastructure created: Vitest (jsdom, @/ alias), Playwright (chromium, webServer), and 4 TDD contract test files with 36 total test cases

## Task Commits

Each task was committed atomically:

1. **Task 01-01: Scaffold Next.js 16 App** — `ad626ce` (feat)
2. **Task 01-02: Install Dependencies** — `c28d969` (feat)
3. **Task 01-03: Configure next.config.ts** — `71c7183` (feat)
4. **Task 01-04: Create Test Infrastructure** — `1346a2f` (test)

## Files Created/Modified
- `apps/web/package.json` — Project manifest with all pinned dependencies
- `apps/web/next.config.ts` — Next.js config wrapped with createNextIntlPlugin()
- `apps/web/i18n/request.ts` — Minimal next-intl request config placeholder
- `apps/web/components.json` — shadcn/ui config (radix-nova, neutral, config="")
- `apps/web/lib/utils.ts` — cn() utility (clsx + tailwind-merge)
- `apps/web/components/ui/button.tsx` — shadcn button component
- `apps/web/app/globals.css` — Tailwind 4 + shadcn design tokens (OKLCH colors)
- `apps/web/vitest.config.ts` — Vitest config (jsdom, @/ alias, tests/**/*.test.ts)
- `apps/web/playwright.config.ts` — Playwright config (chromium, webServer, .spec.ts only)
- `apps/web/tests/design-tokens.test.ts` — 6 assertions for SC-4 (4 pass, 2 fail as expected)
- `apps/web/tests/routes.spec.ts` — 21 route-locale tests for SC-5 (7 routes × 3 locales)
- `apps/web/tests/i18n.spec.ts` — 6 tests for UI-01 (trilingual switching, language switcher)
- `apps/web/tests/fonts.spec.ts` — 3 tests for UI-02 (9 Kazakh chars, Manrope headings, Inter body)

## Decisions Made
- Used radix-nova preset for shadcn (v4.11.0 CLI evolved — "new-york" style renamed to "radix-nova"). Functional equivalent with neutral base color and CSS variables.
- Created minimal i18n/request.ts placeholder because next-intl plugin requires a request config module at build time. Full locale routing and message loading deferred to implementation waves.
- Added testMatch: ['**/*.spec.ts'] to Playwright config to prevent it from attempting to run Vitest .test.ts files (which would error on incompatible imports).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created i18n/request.ts to fix build failure**
- **Found during:** Task 01-03 (Configure next.config.ts with next-intl plugin)
- **Issue:** Build failed with "[next-intl] Could not locate request configuration module" — the next-intl plugin requires an i18n/request.{ts,tsx} file at build time, which the plan did not account for
- **Fix:** Created minimal i18n/request.ts with getRequestConfig returning { locale: 'en', messages: {} }
- **Files modified:** apps/web/i18n/request.ts (new)
- **Verification:** npm run build succeeds
- **Committed in:** 71c7183 (Task 01-03 commit)

**2. [Rule 2 - Missing Critical] Added testMatch filter to Playwright config**
- **Found during:** Task 01-04 (Create test infrastructure)
- **Issue:** Playwright config with testDir: './tests' would match both .spec.ts and .test.ts files, causing import errors when Playwright tries to run Vitest test files
- **Fix:** Added testMatch: ['**/*.spec.ts'] to playwright.config.ts to filter only Playwright spec files
- **Files modified:** apps/web/playwright.config.ts
- **Verification:** Config structure correct — .test.ts files excluded from Playwright runs
- **Committed in:** 1346a2f (Task 01-04 commit)

**3. [Note - CLI Evolution] shadcn style name changed**
- **Found during:** Task 01-02 (Install dependencies)
- **Issue:** Plan specified "style": "new-york" in components.json, but shadcn@4.11.0 uses "style": "radix-nova" (the new-york style was renamed in newer CLI versions)
- **Fix:** Used radix-nova preset with radix base — functional equivalent. The plan's flags (--style, --base-color) no longer exist in v4.11.0; used -b radix -p nova instead
- **Files modified:** apps/web/components.json
- **Verification:** components.json has config="", baseColor=neutral, cssVariables=true — all key requirements met
- **Committed in:** c28d969 (Task 01-02 commit)

---

**Total deviations:** 3 (1 blocking auto-fixed, 1 missing critical auto-fixed, 1 CLI version evolution noted)
**Impact on plan:** All auto-fixes necessary for correct build and test operation. No scope creep.

## Issues Encountered
- shadcn@4.11.0 init is interactive by default — required explicit flags (-b radix -p nova -t next -f) to run non-interactively. The plan's flags (--style, --base-color) are from an older CLI version.

## Known Stubs
- `apps/web/i18n/request.ts` — Returns hardcoded locale 'en' with empty messages. This is a placeholder; full locale routing (ru/kk/en) and message loading will be implemented in subsequent waves of Phase 1. Without this stub, the build fails.

## Next Phase Readiness
- Next.js 16 app is running and building successfully at apps/web/
- next-intl plugin is configured — ready for locale routing and message implementation
- shadcn/ui is initialized — ready for component additions
- Test infrastructure is in place with TDD contract — tests will guide implementation in subsequent waves
- Ready for Plan 01-02 (next plan in Phase 1)

## Self-Check: PASSED

- All 12 key files verified present on disk
- All 4 task commits verified in git log (ad626ce, c28d969, 71c7183, 1346a2f)
- Build verification: npm run build succeeds
- Vitest verification: npx vitest run loads config and runs tests (4 pass, 2 fail as expected TDD)

---
*Phase: 01-app-shell-i18n*
*Completed: 2026-06-25*
