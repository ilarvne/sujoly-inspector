---
phase: 1
slug: app-shell-i18n
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-26
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest (unit/component) + Playwright (e2e) |
| **Config file** | `apps/web/vitest.config.ts` + `apps/web/playwright.config.ts` — Wave 0 installs |
| **Quick run command** | `cd apps/web && npm run build` |
| **Full suite command** | `cd apps/web && npx vitest run && npx playwright test` |
| **Estimated runtime** | ~30 seconds (build) / ~60 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/web && npm run build`
- **After every plan wave:** Run `cd apps/web && npx vitest run && npx playwright test`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

> Populated from 4-plan split (01-01-PLAN through 01-04-PLAN). Per-task verification uses targeted test files (W8) — full Playwright suite runs only in Plan 01-04 (Wave 4).

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01 | 01-01 | 0 | SC-1 | — | N/A | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-02 | 01-01 | 0 | SC-1, SC-4 | — | N/A | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-03 | 01-01 | 0 | SC-1 | — | N/A | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-04 | 01-01 | 0 | UI-01, UI-02, SC-4, SC-5 | — | N/A | unit | `cd apps/web && npx vitest run` | ✅ created | ⬜ pending |
| 01-05 | 01-02 | 1 | UI-01 | — | N/A | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-06 | 01-02 | 1 | UI-01 | V5 Input Validation | Middleware matcher excludes API/static routes | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-07 | 01-02 | 1 | UI-01 | — | N/A | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-08 | 01-02 | 1 | UI-02, SC-3 | V5 Input Validation | hasLocale() validates [locale] segment | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-09 | 01-02 | 2 | SC-4 | — | N/A | unit | `cd apps/web && npx vitest run tests/design-tokens.test.ts` | ✅ created | ⬜ pending |
| 01-10 | 01-03 | 3 | SC-5 | — | N/A | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-11 | 01-03 | 3 | UI-01 | — | N/A | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-12 | 01-03 | 3 | SC-5, UI-01 | — | N/A | smoke | `cd apps/web && npm run build` | N/A | ⬜ pending |
| 01-13 | 01-03 | 3 | SC-5 | — | N/A | e2e | `cd apps/web && npx playwright test tests/routes.spec.ts` | ✅ created | ⬜ pending |
| 01-14 | 01-03 | 3 | UI-01, SC-5 | V5 Input Validation | Invalid locale → 404 | e2e | `cd apps/web && npx playwright test tests/i18n.spec.ts` | ✅ created | ⬜ pending |
| 01-15 | 01-04 | 4 | ALL | — | N/A | full suite | `cd apps/web && npx vitest run && npx playwright test` | ✅ all | ⬜ pending |
| 01-16 | 01-04 | 4 | UI-02, SC-4, UI-01 | — | N/A | manual | (checklist) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/web/vitest.config.ts` — Vitest configuration
- [ ] `apps/web/playwright.config.ts` — Playwright configuration (browsers, baseURL, webServer)
- [ ] `apps/web/tests/i18n.spec.ts` — covers UI-01: language switching, translation rendering
- [ ] `apps/web/tests/routes.spec.ts` — covers SC-5: all 7 routes in all 3 locales return 200
- [ ] `apps/web/tests/fonts.spec.ts` — covers UI-02: Kazakh character rendering (check computed font-family)
- [ ] `apps/web/tests/design-tokens.test.ts` — covers SC-4: verify @theme CSS variables exist
- [ ] Framework install: `cd apps/web && npm install -D vitest @testing-library/react @playwright/test && npx playwright install`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Kazakh character rendering | UI-02 | Font subsetting is build-time; visual verification of actual glyph rendering requires human inspection | Open `/kk` in browser, inspect әғқңөұүһі in DevTools → Computed → font-family. Should show "Inter" or "Manrope", not fallback. |
| Governmental design style | SC-4 | Design aesthetic judgment (color, spacing, typography hierarchy) cannot be fully automated | Visual inspection of home page. Clean, professional, teal-blue primary (#0b4f6c), no playful gradients. |
| Language switcher UX | UI-01 | Navigation behavior and visual transition need human verification | Click switcher, select each locale. Page text changes; URL updates to /ru, /kk, /en. |
| Font weight rendering | UI-02 | Display vs body font assignment is visual | Check headings (Manrope) vs body (Inter) in browser. |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies (16/16 tasks mapped)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every task has build or test verify)
- [x] Wave 0 covers all MISSING references (Plan 01-01 task 01-04 creates all test files)
- [x] No watch-mode flags (all commands use `run`, not `watch`)
- [x] Feedback latency < 60s (build ~30s, targeted tests fast — W8 fix)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready for execution
