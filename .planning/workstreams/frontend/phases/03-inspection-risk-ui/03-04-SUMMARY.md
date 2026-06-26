---
phase: 03-inspection-risk-ui
plan: 04
subsystem: auth
tags: [rbac, zustand, next-intl, shadcn, playwright]

requires:
  - phase: 03-01
    provides: "auth store (useAuthStore), i18n auth namespace, shadcn UI components"
provides:
  - "Login page with 4-role selection (admin, engineer, inspector, viewer)"
  - "LoginForm client component with role cards and sign-in flow"
  - "PermissionGuard component for role-based conditional rendering"
  - "UserMenu component with avatar, role badge, and logout dropdown"
  - "AppShell header integration with UserMenu alongside LanguageSwitcher"
  - "E2E auth flow tests (8 tests covering login, logout, persistence, i18n)"
  - "/login route added to route test coverage (8 routes x 3 locales = 24 tests)"
affects: [03-02, 03-03, 03-05, 03-06]

tech-stack:
  added: []
  patterns:
    - "Server Component page + Client Component child pattern for auth pages"
    - "PermissionGuard wrapping pattern for role-based UI gating"
    - "Zustand persist store consumed by client components for auth state"

key-files:
  created:
    - apps/web/app/[locale]/login/page.tsx
    - apps/web/components/auth/login-form.tsx
    - apps/web/components/auth/permission-guard.tsx
    - apps/web/components/auth/user-menu.tsx
    - apps/web/tests/auth.spec.ts
  modified:
    - apps/web/components/layout/app-shell.tsx
    - apps/web/tests/routes.spec.ts
    - apps/web/messages/kk.json

key-decisions:
  - "Login page renders inside AppShell (with header/sidebar) — user menu shows Sign In when not logged in"
  - "Removed unused UserIcon import from user-menu.tsx to avoid lint warning"
  - "Fixed kk.json duplicate roleViewer key that should have been roleViewerDesc (data error from 03-01)"

patterns-established:
  - "PermissionGuard: <PermissionGuard roles={['admin', 'engineer']}>{children}</PermissionGuard> for role gating"
  - "UserMenu auto-renders Sign In button when user is null, dropdown when logged in"

requirements-completed: [RISK-07-FE]

coverage:
  - id: D1
    description: "Login page at /[locale]/login with 4 role selection cards (admin, engineer, inspector, viewer)"
    requirement: "RISK-07-FE"
    verification:
      - kind: e2e
        ref: "tests/auth.spec.ts#Login page renders with 4 role cards"
        status: pass
      - kind: e2e
        ref: "tests/auth.spec.ts#Login page works in English"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sign in navigates to /map with user menu visible in header"
    requirement: "RISK-07-FE"
    verification:
      - kind: e2e
        ref: "tests/auth.spec.ts#Sign in navigates to /map"
        status: pass
    human_judgment: false
  - id: D3
    description: "User menu shows user name, role badge, and logout dropdown in app shell header"
    requirement: "RISK-07-FE"
    verification:
      - kind: e2e
        ref: "tests/auth.spec.ts#User menu shows user name and logout"
        status: pass
    human_judgment: false
  - id: D4
    description: "Logout clears auth state and navigates to /login"
    requirement: "RISK-07-FE"
    verification:
      - kind: e2e
        ref: "tests/auth.spec.ts#Logout navigates to login"
        status: pass
    human_judgment: false
  - id: D5
    description: "Auth state persists across page navigation via Zustand persist (localStorage)"
    requirement: "RISK-07-FE"
    verification:
      - kind: e2e
        ref: "tests/auth.spec.ts#Auth persists across navigation"
        status: pass
    human_judgment: false
  - id: D6
    description: "PermissionGuard component for role-based conditional rendering"
    requirement: "RISK-07-FE"
    verification:
      - kind: other
        ref: "npm run build — TypeScript compiles, component exported"
        status: pass
    human_judgment: false
  - id: D7
    description: "Not logged in users see Sign In link in header"
    requirement: "RISK-07-FE"
    verification:
      - kind: e2e
        ref: "tests/auth.spec.ts#Not logged in shows sign-in link"
        status: pass
    human_judgment: false
  - id: D8
    description: "/login route accessible in all 3 locales (ru, kk, en)"
    requirement: "RISK-07-FE"
    verification:
      - kind: e2e
        ref: "tests/routes.spec.ts — /login route in 3 locales"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-06-26
status: complete
---

# Plan 03-04: Mock RBAC Auth UI Summary

**Login page with 4-role selection, user menu with logout in app shell header, and PermissionGuard for role-based UI gating**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3
- **Files modified:** 8 (5 created, 3 modified)

## Accomplishments
- Login page at `/[locale]/login` with 4 role cards (admin, engineer, inspector, viewer) and sign-in button
- UserMenu in app shell header showing avatar initials, name, role badge, and logout dropdown — or Sign In link when not logged in
- PermissionGuard component for conditional rendering based on user role
- Auth state persists across navigation via Zustand persist middleware (localStorage)
- 8 E2E auth tests covering login, role selection, navigation, user menu, logout, persistence, and i18n

## Task Commits

1. **Task 1: Login page, login form, permission guard** - `c1f0088` (feat)
2. **Task 2: User menu and app shell integration** - `71f8510` (feat)
3. **Task 3: E2E auth tests and route test update** - `1c819fc` (test)
4. **Fix: kk.json duplicate key** - `d93e9bb` (fix)

## Files Created/Modified
- `apps/web/app/[locale]/login/page.tsx` - Server Component login page with getTranslations('auth')
- `apps/web/components/auth/login-form.tsx` - Client component with 4 role cards and sign-in button calling useAuthStore.login()
- `apps/web/components/auth/permission-guard.tsx` - Role-based conditional rendering wrapper using useAuthStore.hasRole()
- `apps/web/components/auth/user-menu.tsx` - Header dropdown with avatar, name, role badge, and logout; Sign In button when not logged in
- `apps/web/components/layout/app-shell.tsx` - Header modified to include UserMenu alongside LanguageSwitcher
- `apps/web/tests/auth.spec.ts` - 8 Playwright E2E tests for auth flow
- `apps/web/tests/routes.spec.ts` - Added '/login' to routes array (now 8 routes x 3 locales)
- `apps/web/messages/kk.json` - Fixed duplicate roleViewer key → roleViewerDesc

## Decisions Made
- Login page renders inside AppShell (with header/sidebar visible) — user menu shows Sign In button when not logged in, which is the simplest approach for an MVP mock auth
- Removed unused `UserIcon` import from user-menu.tsx (plan included it but it was not used in the final component)

## Deviations from Plan

### Auto-fixed Issues

**1. [Data Error] kk.json duplicate roleViewer key should be roleViewerDesc**
- **Found during:** Post-build verification (Task 1)
- **Issue:** kk.json had two `"roleViewer"` keys — the second (line 207) should have been `"roleViewerDesc"`, causing `MISSING_MESSAGE: auth.roleViewerDesc (kk)` during static generation
- **Fix:** Changed duplicate `"roleViewer"` to `"roleViewerDesc"` in kk.json
- **Files modified:** apps/web/messages/kk.json
- **Verification:** Build passes cleanly with no MISSING_MESSAGE errors
- **Committed in:** d93e9bb

---

**Total deviations:** 1 auto-fixed (1 data error from Plan 03-01)
**Impact on plan:** Minor fix to pre-existing i18n data error. No scope creep.

## Issues Encountered
- `.next/dev/types/routes.d.ts` was corrupted on first rebuild attempt (truncated `Record` type). Resolved by clearing `.next` directory and rebuilding — transient build cache issue, not a code problem.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- PermissionGuard is ready for Plan 03-02's engineer override button to wrap with `<PermissionGuard roles={['admin', 'engineer']}>`
- UserMenu is integrated and functional in all routes
- Auth store persists across refreshes — field-ready for offline PWA scenarios
- All Phase 1-2 tests still pass (routes.spec.ts expanded to include /login)

---
*Phase: 03-inspection-risk-ui*
*Completed: 2026-06-26*
