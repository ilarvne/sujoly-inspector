---
phase: 03-risk-models-inspection-logic
plan: 06
subsystem: backend
tags: [export, csv, geojson, pdf, weasyprint, jinja2, trilingual, risk]
dependency_graph:
  requires: [03-03, 03-05]
  provides: [export-endpoints]
  affects: [export-service, export-routes, export-templates]
tech-stack:
  added: [weasyprint, jinja2]
  patterns: [streaming-csv-with-bom, featurecollection-geojson, weasyprint-pdf-with-asyncio-to-thread, csv-formula-injection-mitigation]
key-files:
  created:
    - apps/api/src/api/services/export_service.py
    - apps/api/src/api/routes/exports.py
    - apps/api/src/api/schemas/exports.py
    - apps/api/templates/inspection_report_ru.html
    - apps/api/templates/inspection_report_kk.html
    - apps/api/templates/inspection_report_en.html
  modified:
    - apps/api/tests/test_exports.py
decisions:
  - CSV export uses StreamingResponse with UTF-8 BOM for Excel Cyrillic compatibility (D-20)
  - GeoJSON export reuses existing FeatureCollection pattern from structures endpoint (D-21)
  - PDF uses WeasyPrint + Jinja2 with asyncio.to_thread() for non-blocking generation (D-22, T-03-20)
  - Trilingual labels via server-side _TRANSLATIONS dict, not next-intl (D-23)
  - CSV formula injection mitigated by prefixing =,+,-,@ cells with single quote (T-03-18)
  - Dockerfile already had WeasyPrint system deps from Plan 03-02 — no change needed
metrics:
  duration: 5min
  tasks: 2
  files: 7
---

# Phase 03 Plan 06: Trilingual Export Endpoints Summary

Trilingual export endpoints (CSV/GeoJSON/PDF) with UTF-8 BOM, WeasyPrint PDF generation, and server-side translations dict for all labels in Russian, Kazakh, and English.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | RED — Write failing tests for export endpoints | ae7f127 | apps/api/tests/test_exports.py |
| 2 | GREEN — Implement export service, routes, templates, schemas | 3d78efa | apps/api/src/api/services/export_service.py, apps/api/src/api/routes/exports.py, apps/api/src/api/schemas/exports.py, apps/api/templates/inspection_report_{ru,kk,en}.html |

## Key Artifacts

| Symbol | Type | File | Purpose |
|--------|------|------|---------|
| `export_structures_csv()` | function | export_service.py | CSV export with StreamingResponse + UTF-8 BOM (D-20) |
| `export_structures_geojson()` | function | export_service.py | GeoJSON FeatureCollection with risk fields (D-21) |
| `export_inspection_report_pdf()` | function | export_service.py | PDF via WeasyPrint + Jinja2 (D-22) |
| `_TRANSLATIONS` | dict | export_service.py | Trilingual labels ru/kk/en (D-23) |
| `_sanitize_csv_cell()` | function | export_service.py | CSV formula injection mitigation (T-03-18) |
| `ExportParams` | schema | schemas/exports.py | Query parameter validation |
| `GET /api/v1/export/structures` | endpoint | routes/exports.py | CSV/GeoJSON export (D-19) |
| `GET /api/v1/export/inspection-report/{id}` | endpoint | routes/exports.py | PDF inspection report (D-19) |

## Verification

- 10/10 export tests pass
- 135/136 full suite tests pass (1 pre-existing provenance FK test failure unrelated to this plan)
- CSV export returns UTF-8 BOM, trilingual headers, risk fields
- GeoJSON export returns FeatureCollection with risk properties
- PDF endpoint returns 200 for valid inspection, 404 for nonexistent
- Trilingual support verified for ru/kk/en

## Deviations from Plan

None — plan executed exactly as written.

Dockerfile WeasyPrint deps were already present from Plan 03-02; Task 1 action for Dockerfile update was a no-op (already satisfied).

## Threat Flags

No new threat surface beyond what the plan's threat_model covers. All four STRIDE mitigations implemented:
- T-03-18 (CSV formula injection): `_sanitize_csv_cell()` prefixes dangerous chars
- T-03-19 (bbox injection): Reuses `_apply_bbox_filter` from structure_service
- T-03-20 (PDF blocks event loop): `asyncio.to_thread()` for WeasyPrint call
- T-03-21 (PDF photo data): Accepted — photos are inspection evidence gated by RBAC

## Self-Check: PASSED

All files and commits verified present.
