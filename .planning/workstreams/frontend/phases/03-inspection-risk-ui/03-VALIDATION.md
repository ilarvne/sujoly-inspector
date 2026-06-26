---
phase: 3
slug: inspection-risk-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-26
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest (unit/logic) + Playwright (E2E/feature rendering) |
| **Config file** | `apps/web/vitest.config.ts` (existing) + `apps/web/playwright.config.ts` (existing) |
| **Quick run command** | `cd apps/web && npx vitest run` |
| **Full suite command** | `cd apps/web && npx vitest run && npx playwright test` |
| **Estimated runtime** | ~120 seconds |

**Key constraints:**
- jsdom (Vitest) does NOT support WebGL or browser download APIs. Export/PDF generation tested via Playwright E2E only.
- jsdom does NOT support localStorage. Auth store persistence tested via Playwright E2E only.
- Unit tests cover: mock data logic (inspections, documents, risk scores, overrides), Zustand store actions (auth store), TypeScript type validation, export utility pure functions (CSV string generation, GeoJSON serialization).

---

## Sampling Rate

- **After every task commit:** Run `cd apps/web && npm run build`
- **After every plan wave:** Run `cd apps/web && npx vitest run && npx playwright test`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | 03-01 | 1 | DATA-05-FE | T-03-01 | Mock data types validated | unit | `npx vitest run tests/phase3-mocks.test.ts` | No | pending |
| TBD | 03-01 | 1 | RISK-07-FE | T-03-02 | Auth store actions tested | unit | `npx vitest run tests/phase3-mocks.test.ts -g "auth"` | No | pending |
| TBD | 03-02 | 2 | DATA-05-FE | T-03-01 | Inspection timeline renders | e2e | `npx playwright test tests/inspection.spec.ts` | No | pending |
| TBD | 03-02 | 2 | SC-3 | T-03-01 | Risk score display renders | e2e | `npx playwright test tests/inspection.spec.ts -g "risk"` | No | pending |
| TBD | 03-02 | 2 | RISK-06-FE | T-03-03 | Override dialog opens for engineer | e2e | `npx playwright test tests/inspection.spec.ts -g "override"` | No | pending |
| TBD | 03-03 | 3 | DATA-06-FE | T-03-04 | Document upload UI renders | e2e | `npx playwright test tests/documents.spec.ts` | No | pending |
| TBD | 03-04 | 2 | RISK-07-FE | T-03-02 | Login page renders, role selection works | e2e | `npx playwright test tests/auth.spec.ts` | No | pending |
| TBD | 03-04 | 2 | RISK-07-FE | T-03-02 | Permission gating hides/shows UI | e2e | `npx playwright test tests/auth.spec.ts -g "permission"` | No | pending |
| TBD | 03-05 | 2 | RISK-08-FE | T-03-05 | Export panel renders with format options | e2e | `npx playwright test tests/export.spec.ts` | No | pending |
| TBD | 03-05 | 2 | RISK-08-FE | T-03-05 | CSV export downloads file | e2e | `npx playwright test tests/export.spec.ts -g "csv"` | No | pending |
| TBD | 03-05 | 2 | RISK-08-FE | T-03-05 | PDF export downloads file | e2e | `npx playwright test tests/export.spec.ts -g "pdf"` | No | pending |
| TBD | 03-05 | 2 | — | — | Export utility functions produce valid output | unit | `npx vitest run tests/export-utils.test.ts` | No | pending |

*Status: pending / green / red / flaky*

*Task IDs will be filled from PLAN.md after planner completes.*

---

## Wave 0 Requirements

- [ ] `apps/web/tests/phase3-mocks.test.ts` — covers mock data: inspections, documents, risk scores, overrides, auth store
- [ ] `apps/web/tests/inspection.spec.ts` — covers DATA-05-FE, SC-3, RISK-06-FE: inspection timeline, risk display, override dialog
- [ ] `apps/web/tests/documents.spec.ts` — covers DATA-06-FE: document upload, document list
- [ ] `apps/web/tests/auth.spec.ts` — covers RISK-07-FE: login, role selection, permission gating
- [ ] `apps/web/tests/export.spec.ts` — covers RISK-08-FE: CSV/GeoJSON/PDF export
- [ ] `apps/web/tests/export-utils.test.ts` — covers export utility pure functions (CSV string, GeoJSON string)
- [ ] shadcn/ui components installed: `npx shadcn@latest add dialog tabs table tooltip alert textarea label input progress accordion dropdown-menu avatar scroll-area`

*Existing tests from Phases 1-2: routes.spec.ts, i18n.spec.ts, fonts.spec.ts, design-tokens.test.ts, mock-data.test.ts, stores.test.ts, types.test.ts, map.spec.ts, passport.spec.ts, dashboard.spec.ts, filter.spec.ts — all must still pass*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PDF visual layout quality | RISK-08-FE | PDF rendering cannot be visually inspected by automated tests | Generate PDF export, open in PDF viewer, verify Cyrillic text renders correctly (or transliteration is readable) |
| File upload UX flow | DATA-06-FE | Drag-and-drop interaction is hard to automate reliably | Manually drag a file onto the upload area, verify it appears in the list |
| Role permission visual gating | RISK-07-FE | Visual inspection of what's hidden/shown per role | Login as each role, verify correct UI elements are visible/hidden |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
