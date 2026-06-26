# Phase 5: PWA Field Mode - Validation

**Created:** 2026-06-26

## UAT Criteria

| # | Requirement | Validation Method | Status |
|---|-------------|-------------------|--------|
| 1 | FIELD-01: PWA installable, works offline | Build produces sw.js + manifest.json. SW registered in production. Offline page accessible. | Pending |
| 2 | FIELD-02: Offline capture (photos, voice, GPS, forms) | /field page renders form. Photo capture works. Voice recording works. GPS correction works. Data saved to IndexedDB. | Pending |
| 3 | FIELD-03: Deferred sync with field-level merge | Sync engine processes queue on 'online'. Conflict resolution dialog shows field-by-field comparison. | Pending |
| 4 | FIELD-04: Voice transcription post-sync | Voice notes get transcription status. Mock transcription returns text. | Pending |
| 5 | FIELD-05: Per-record sync status + conflict UI | Sync status badge per record. Sync queue panel. Conflict resolution dialog. | Pending |

## Build Verification

- `npm run build` passes without errors
- `npx vitest run` passes all unit tests
- Service worker file (sw.js) generated in public/
- manifest.json present in public/
- All 3 message files have new namespaces (field, sync, pwa)

## Regression Checks

- All Phase 1-3 tests still pass
- All existing routes still work (/, /dashboard, /map, /objects, /copilot, /reports, /hydrofinder, /login)
- No i18n key regressions
- Design system tokens unchanged
