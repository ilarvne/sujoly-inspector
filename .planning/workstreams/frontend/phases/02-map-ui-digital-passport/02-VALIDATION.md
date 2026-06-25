---
phase: 2
slug: map-ui-digital-passport
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-26
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest (unit/logic) + Playwright (E2E/map rendering) |
| **Config file** | `apps/web/vitest.config.ts` (existing) + `apps/web/playwright.config.ts` (existing) |
| **Quick run command** | `cd apps/web && npx vitest run` |
| **Full suite command** | `cd apps/web && npx vitest run && npx playwright test` |
| **Estimated runtime** | ~90 seconds |

**Key constraint:** jsdom (Vitest environment) does NOT support WebGL. MapLibre components cannot be unit-tested with Vitest. Map rendering must be tested via Playwright E2E only. Unit tests cover: mock data logic, filter functions, Zustand store actions, TypeScript type validation, and data transformations.

---

## Sampling Rate

- **After every task commit:** Run `cd apps/web && npm run build`
- **After every plan wave:** Run `cd apps/web && npx vitest run && npx playwright test`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | MAP-01 | — | N/A | e2e | `npx playwright test tests/map.spec.ts` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | MAP-02 | — | N/A | e2e | `npx playwright test tests/map.spec.ts -g "colors"` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | MAP-03 | — | N/A | e2e | `npx playwright test tests/map.spec.ts -g "passport"` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | MAP-04 | — | N/A | e2e | `npx playwright test tests/dashboard.spec.ts` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | MAP-05 | — | N/A | e2e | `npx playwright test tests/filter.spec.ts` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | DATA-04 | — | N/A | e2e | `npx playwright test tests/passport.spec.ts` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | MOCK | — | N/A | unit | `npx vitest run tests/mock-data.test.ts` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | STORE | — | N/A | unit | `npx vitest run tests/stores.test.ts` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | TYPES | — | N/A | unit | `npx vitest run tests/types.test.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Task IDs will be filled from PLAN.md after planner completes.*

---

## Wave 0 Requirements

- [ ] `apps/web/tests/map.spec.ts` — covers MAP-01, MAP-02, MAP-03: map renders, structures visible, color-coded, click opens passport
- [ ] `apps/web/tests/dashboard.spec.ts` — covers MAP-04: dashboard charts render, show data
- [ ] `apps/web/tests/filter.spec.ts` — covers MAP-05: filter controls work, affect map and dashboard
- [ ] `apps/web/tests/passport.spec.ts` — covers DATA-04: passport shows all required sections
- [ ] `apps/web/tests/mock-data.test.ts` — covers MOCK: valid GeoJSON, filter correctness, edge cases (empty results, missing coords)
- [ ] `apps/web/tests/stores.test.ts` — covers STORE: Zustand store actions
- [ ] `apps/web/tests/types.test.ts` — covers TYPES: TypeScript type validation
- [ ] shadcn/ui components install: `npx shadcn@latest add sheet select checkbox badge separator card` — if not already present from Phase 1

*Existing tests from Phase 1: routes.spec.ts (21 tests), i18n.spec.ts (6 tests), fonts.spec.ts (3 tests), design-tokens.test.ts (6 tests) — all must still pass*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Map visual rendering quality | MAP-01 | WebGL rendering cannot be visually inspected by automated tests | Open /map in browser, verify structures appear at expected geographic positions in Zhambyl Oblast |
| Color-coded symbology visual accuracy | MAP-02 | Color perception is subjective; automated tests check CSS values but not visual rendering | Verify green/yellow/orange/red/gray markers match status colors on map |
| Tile loading performance | MAP-01 | Network-dependent, varies by environment | Check map tiles load within 2-3 seconds at zoom level 7 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
