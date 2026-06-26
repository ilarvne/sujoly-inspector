# Plan 03-03 Summary: Document Management UI

## Plan
03-03 — Document Upload and List in Passport Panel Documents Tab

## Tasks Completed

### Task 1: Implement document upload and document list components
- **Commit:** `3ffbed9`
- Created `apps/web/components/documents/document-upload.tsx` — drag-and-drop upload area with click-to-browse, PDF/JPG/PNG type validation, 10MB size limit, upload progress simulation (Progress bar), error/success Alert messages, queryClient invalidation on upload complete
- Created `apps/web/components/documents/document-list.tsx` — table with filename, type badge, human-readable file size, uploaded by, uploaded date (date-fns formatted), download link anchor; loading and empty states; uses `useDocuments` hook

### Task 2: Wire document components into passport panel Documents tab and E2E test
- **Commit:** `6171d91`
- Modified `apps/web/components/map/passport-panel.tsx` — replaced Documents tab placeholder stub with `<DocumentUpload>` and `<DocumentList>` components, removed unused `tDocs` translation hook
- Created `apps/web/tests/documents.spec.ts` — 2 E2E tests: Documents tab upload area visible in RU locale, Documents tab upload area visible in EN locale; uses proven `openPassport` helper pattern from inspection.spec.ts

## Key Deliverables
| File | Type | Description |
|------|------|-------------|
| `apps/web/components/documents/document-upload.tsx` | new | Drag-and-drop file upload with validation and progress simulation |
| `apps/web/components/documents/document-list.tsx` | new | Document table with metadata and download links |
| `apps/web/components/map/passport-panel.tsx` | modified | Documents tab now renders real components instead of placeholder |
| `apps/web/tests/documents.spec.ts` | new | E2E tests for Documents tab in RU and EN locales |

## Commit Hashes
1. `3ffbed9` — feat(documents): add DocumentUpload and DocumentList components
2. `6171d91` — feat(documents): wire DocumentUpload and DocumentList into passport panel

## Deviations
- Removed unused `Button` import from document-upload.tsx (plan's sample code imported it but never used it — would cause lint/TS unused import error)
- Removed unused `tDocs` translation hook from passport-panel.tsx after replacing the placeholder that was its only consumer
- E2E tests use the proven `openPassport`/`clickStructureAt`/`waitForMapReady` helper pattern from inspection.spec.ts instead of the plan's simpler center-click approach (more reliable against map projection)
- `mockAddDocument` return value is not stored in a variable (plan assigned it to `newDoc` but never used it — removed to avoid unused variable lint error)

## Requirements Met
- **DATA-06-FE:** Documents tab in passport panel shows document upload area and document list
- Upload accepts file selection via click-to-browse or drag-and-drop
- Upload validates file type (PDF, JPG, PNG) and size (max 10MB)
- Upload simulates presigned URL flow — shows uploading state then success
- Document list shows all attached documents with filename, type, size, uploaded by, uploaded date
- Each document has a download link (mock URL)
- Invalid file type or oversize file shows error alert
- Empty state shows when no documents are attached
- All labels translated in all 3 locales (documents namespace — keys already present from Wave 1)
