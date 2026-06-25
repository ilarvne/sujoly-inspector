---
phase: 1
slug: app-shell-i18n
status: draft
nyquist_compliant: false
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

> Tasks not yet planned. This table will be populated after PLAN.md creation by the gsd-planner.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| _TBD_ | _TBD_ | _TBD_ | UI-01 | V5 Input Validation | hasLocale() validates [locale] segment | e2e | `npx playwright test tests/i18n.spec.ts` | ❌ W0 | ⬜ pending |
| _TBD_ | _TBD_ | _TBD_ | UI-01 | — | N/A | e2e | `npx playwright test tests/routes.spec.ts` | ❌ W0 | ⬜ pending |
| _TBD_ | _TBD_ | _TBD_ | UI-02 | — | N/A | e2e + manual | `npx playwright test tests/fonts.spec.ts` | ❌ W0 | ⬜ pending |
| _TBD_ | _TBD_ | _TBD_ | SC-4 | — | N/A | unit | `npx vitest run tests/design-tokens.test.ts` | ❌ W0 | ⬜ pending |
| _TBD_ | _TBD_ | _TBD_ | SC-5 | — | N/A | e2e | `npx playwright test tests/routes.spec.ts` | ❌ W0 | ⬜ pending |

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
