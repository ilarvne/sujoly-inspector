---
phase: 04-discovery-matching-backend
plan: 03
subsystem: api, geospatial, ocr
tags: [stac, titiler, cog, minio, ocr, russian, kazakh, entity-extraction, fastapi]

# Dependency graph
requires:
  - phase: 04-01
    provides: CandidateModel, matching service
  - phase: 04-02
    provides: MinIOService, DocumentModel, document service
provides:
  - StacService with collection CRUD, item management, bbox search, TiTiler URL generation
  - OcrService with text extraction, Russian/Kazakh entity patterns, document processing
  - STAC REST endpoints (6 routes)
  - OCR REST endpoints (3 routes)
affects: [04-04, frontend-map, frontend-evidence-panel]

# Tech tracking
tech-stack:
  added: [stac-service, ocr-service]
  patterns: [in-minio-json-catalog, pattern-matching-ocr, entity-extraction-ru-kk]

key-files:
  created:
    - apps/api/src/api/services/stac_service.py
    - apps/api/src/api/routes/stac.py
    - apps/api/src/api/services/ocr_service.py
    - apps/api/src/api/routes/ocr.py
    - apps/api/tests/test_stac.py
    - apps/api/tests/test_ocr.py
  modified: []

key-decisions:
  - "STAC catalog stored as JSON in MinIO (not full STAC server) — lightweight for hackathon MVP"
  - "TiTiler URL template with presigned MinIO URL for COG access"
  - "OCR service uses pattern-matching stub (not Tesseract/EasyOCR) — upgrade path preserved"
  - "Entity extraction via regex for Russian/Kazakh hydraulic passport fields"
  - "OCR results cached in-memory for MVP; production would use DB"

patterns-established:
  - "In-MinIO JSON catalog: collections/items stored as JSON objects in MinIO buckets"
  - "Hasattr guard for release_conn: MinIO SDK response has release_conn but BytesIO mock doesn't"
  - "Russian/Kazakh bilingual entity patterns: both Наименование/Атауы, Район/Аудан, Состояние/Жағдай"

requirements-completed: []

# Metrics
duration: 4min
completed: 2026-06-26
---

# Phase 04 Plan 03: STAC Catalog + OCR Pipeline Summary

**STAC catalog service with MinIO-backed JSON storage + TiTiler URL generation, OCR pipeline with Russian/Kazakh entity extraction for scanned passports**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-26T03:51:15Z
- **Completed:** 2026-06-26T03:55:53Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- STAC catalog service: create_collection, add_item, search_items (with bbox filter), get_titiler_url, list_collections, list_items
- Lightweight STAC-like catalog stored as JSON in MinIO sujoly-imagery bucket
- TiTiler URL generation: http://titiler:8081/cog/tiles/{z}/{x}/{y}.png?url={presigned_cog_url}
- OCR service: extract_text (HIGH for text files, LOW stub for images/PDFs), extract_entities (6 entity types)
- Russian/Kazakh entity patterns: structure_name, commissioning_year, district, condition, water_source, capacity
- All 41 tests passing (16 STAC + 25 OCR)

## Task Commits

Each task was committed atomically:

1. **Task 1: STAC catalog service and endpoints** - `c535053` (feat)
2. **Task 2: OCR pipeline service and endpoints** - `ab9efa4` (feat)

## Files Created/Modified
- `apps/api/src/api/services/stac_service.py` - STAC catalog service with MinIO JSON storage, bbox search, TiTiler URL generation
- `apps/api/src/api/routes/stac.py` - STAC REST endpoints (6 routes: collections CRUD, items, search, tiles)
- `apps/api/tests/test_stac.py` - STAC service unit tests + endpoint integration tests (16 tests)
- `apps/api/src/api/services/ocr_service.py` - OCR service with text extraction, Russian/Kazakh entity patterns
- `apps/api/src/api/routes/ocr.py` - OCR REST endpoints (3 routes: upload, process, results)
- `apps/api/tests/test_ocr.py` - OCR service unit tests + endpoint integration tests (25 tests)

## Decisions Made
- STAC catalog stored as JSON in MinIO (not full STAC server) — lightweight for hackathon MVP, upgrade path to stac-fastapi preserved
- TiTiler URL template includes presigned MinIO URL for COG access — production would use internal S3 endpoint
- OCR service uses pattern-matching stub (not Tesseract/EasyOCR) — upgrade path preserved, confidence=LOW for images
- Entity extraction via regex for Russian/Kazakh hydraulic passport fields — covers 6 entity types with bilingual prefixes
- OCR results cached in-memory for MVP; production would store in document metadata or separate table

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added hasattr guard for MinIO response.release_conn()**
- **Found during:** Task 1 (STAC service tests)
- **Issue:** BytesIO mock returned by test doesn't have release_conn() method that real MinIO SDK responses have
- **Fix:** Added `if hasattr(response, "release_conn"): response.release_conn()` guard in all get_object cleanup paths
- **Files modified:** apps/api/src/api/services/stac_service.py
- **Verification:** All 16 STAC tests pass
- **Committed in:** c535053 (part of Task 1 commit)

**2. [Rule 3 - Blocking] Fixed mock list_objects to synthesize directory entries**
- **Found during:** Task 1 (STAC list_collections test)
- **Issue:** MinIO list_objects with recursive=False returns directory-style entries ending with /, but the mock only returned stored file keys
- **Fix:** Updated mock to synthesize directory prefixes when recursive=False, matching real MinIO behavior
- **Files modified:** apps/api/tests/test_stac.py
- **Verification:** All 16 STAC tests pass
- **Committed in:** c535053 (part of Task 1 commit)

**3. [Rule 1 - Bug] Fixed Kazakh language detection test to use actual Kazakh-specific characters**
- **Found during:** Task 2 (OCR Kazakh detection test)
- **Issue:** Test text "Бигаз каналы" contains only standard Cyrillic, not Kazakh-specific characters (ә, ғ, қ, ң, ө, ұ, ү, һ, і)
- **Fix:** Changed test text to include "Өзен" which contains the Kazakh-specific letter Ө
- **Files modified:** apps/api/tests/test_ocr.py
- **Verification:** All 25 OCR tests pass
- **Committed in:** ab9efa4 (part of Task 2 commit)

**4. [Rule 3 - Blocking] Mocked OcrService.process_document for not-found test**
- **Found during:** Task 2 (OCR process_document_not_found endpoint test)
- **Issue:** Test tried to call real async_session which attempted real DB connection, causing gaierror
- **Fix:** Patched OcrService.process_document to raise ValueError, matching the service's not-found behavior
- **Files modified:** apps/api/tests/test_ocr.py
- **Verification:** All 25 OCR tests pass
- **Committed in:** ab9efa4 (part of Task 2 commit)

---

**Total deviations:** 4 auto-fixed (2 bugs, 2 blocking)
**Impact on plan:** All auto-fixes necessary for test correctness. No scope creep.

## Issues Encountered
None — all deviations were caught and fixed during test execution.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- STAC catalog service ready for frontend integration (map evidence panel)
- OCR pipeline ready for document upload workflow
- Plan 04-04 next: remaining discovery/matching backend tasks

---
*Phase: 04-discovery-matching-backend*
*Completed: 2026-06-26*
