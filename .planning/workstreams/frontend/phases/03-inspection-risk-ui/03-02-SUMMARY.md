# Plan 03-02 Summary: Inspection Timeline, Risk Score Display, and Engineer Override Dialog

## Plan
03-02 — Phase 3 Wave 2: Inspection & Risk UI components

## Tasks Completed

### Task 1: Refactor passport panel with Tabs and implement inspection timeline
- **Commit**: `30ff6ba`
- **Files**:
  - `apps/web/components/inspection/inspection-timeline.tsx` — Vertical timeline of inspection records with date, inspector, findings, photos, condition badge
  - `apps/web/components/map/passport-panel.tsx` — Refactored with 4 Tabs (Overview, Inspections, Risk, Documents)
- **Key changes**:
  - Passport panel now uses shadcn/ui Tabs with 4 tabs
  - Overview tab retains all Phase 2 content (identity, geometry, admin location, technical specs, status, provenance)
  - Inspections tab renders InspectionTimeline with ScrollArea, loading/empty states
  - Risk tab renders RiskScoreDisplay (from Task 2)
  - Documents tab shows placeholder stub (filled by Plan 03-03)
  - Inspection timeline uses date-fns for date formatting, STATUS_COLORS_HEX for condition badges

### Task 2: Implement risk score display and engineer override dialog
- **Commit**: `cbffe73`
- **Files**:
  - `apps/web/components/inspection/risk-score-display.tsx` — Risk score gauge, component breakdown, explanation, override button
  - `apps/web/components/override/engineer-override-dialog.tsx` — Engineer override form dialog with validation and provenance log
- **Key changes**:
  - RiskScoreDisplay: overall score as Progress bar (0-100), risk level badge (HIGH/MEDIUM/LOW), component breakdown with Accordion (4 components), explanation text
  - Override button visible only to admin/engineer roles via useAuthStore.hasRole
  - EngineerOverrideDialog uses react-hook-form with zodResolver for validation
  - Zod schema: reason must be >= 10 characters, newValue must be non-empty
  - Dialog has field Select (inspection_interval, repair_status), read-only original value, new value Input, reason Textarea
  - Provenance log shows override history with field, original → new value, reason, engineer name, timestamp
  - Fixed plan's hooks violation (useTranslations called inside JSX) by declaring tOverride at component top

### Task 3: E2E test for inspection timeline, risk display, and override dialog
- **Commit**: `7a3c030`
- **Files**:
  - `apps/web/tests/inspection.spec.ts` — 6 Playwright E2E tests
- **Tests**:
  1. Passport has 4 tabs after clicking structure (Russian labels)
  2. Inspections tab shows timeline with inspector entries
  3. Risk tab shows overall score and component breakdown
  4. Override button hidden without login, visible for engineer role (auth store via localStorage)
  5. Override dialog opens with form fields and provenance log
  6. Inspection and risk tabs work in English locale

## Verification
- `npm run build` — PASSED (TypeScript compilation + static page generation, 27/27 pages)
- Build time: ~8.4s compile, 11.5s TypeScript check

## Commit Hashes
| Task | Commit | Description |
|------|--------|-------------|
| 1 | `30ff6ba` | Passport panel Tabs + inspection timeline |
| 2 | `cbffe73` | Risk score display + engineer override dialog |
| 3 | `7a3c030` | E2E tests for inspection/risk/override |

## Key Deliverables
- Passport panel refactored with 4 Tabs (Overview, Inspections, Risk, Documents)
- InspectionTimeline component with vertical timeline, date-fns formatting, condition badges
- RiskScoreDisplay with Progress gauge, Accordion breakdown, role-gated override button
- EngineerOverrideDialog with react-hook-form + zod validation, provenance log
- 6 E2E tests covering tab navigation, timeline rendering, risk display, role gating, dialog

## Deviations from Plan
- **risk-score-display.tsx**: Fixed React hooks violation — plan called `useTranslations('override')('title')` inside JSX which violates rules of hooks. Declared `tOverride` at component top level instead.
- **engineer-override-dialog.tsx**: Used react-hook-form's `useForm` with `zodResolver` properly (register, handleSubmit, watch, setValue, formState.errors) instead of plan's manual useState validation approach. This satisfies the artifact requirement (`contains: "useForm"`) and is cleaner.
- **engineer-override-dialog.tsx**: Removed unused `useAuthStore` import and `user` variable (role gating is handled in RiskScoreDisplay, not the dialog).
- **risk-score-display.tsx**: Omitted unused Tooltip imports from plan (plan imported but never used them).
- **passport-panel.tsx**: Added `tDocs` translator for Documents tab placeholder text using `documents.noDocuments` translation key instead of empty div.

## Requirements Met
- DATA-05-FE: Inspection timeline with historical records
- RISK-06-FE: Engineer override with provenance log
