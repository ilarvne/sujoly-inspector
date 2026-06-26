---
phase: 1
plan: api-integration
subsystem: frontend
tags: [api, frontend, real-data, copilot, bugfix]
requires:
  - Backend API running at localhost:8000
  - PostgreSQL with PostGIS data ingested
provides:
  - Real API data flowing to all frontend hooks
  - Copilot chat using backend LLM instead of mock engine
affects:
  - apps/web/lib/api/client.ts
  - apps/web/lib/stores/chat-store.ts
  - apps/api/src/api/schemas/structures.py
tech-stack:
  added: []
  patterns: [bearer-token-auth, graceful-error-fallback, field-validator-wkb]
key-files:
  created: []
  modified:
    - apps/web/lib/api/client.ts
    - apps/web/lib/stores/chat-store.ts
    - apps/api/src/api/schemas/structures.py
decisions:
  - Used format=geojson API parameter for structures to get geometry directly
  - Mapped Russian technical_condition abbreviations (удов/неуд/авар) to ConditionStatus
  - Auth token cached in module scope, refreshed on 401
  - EWKB parsed without shapely dependency using struct.unpack
metrics:
  duration: ~20min
  completed: 2026-06-26T06:30:00Z
  tasks: 2
  files: 3
---

# Phase 1 Plan api-integration: Replace Mock Data with Real API Calls Summary

Real backend API integration for all frontend data hooks and copilot chat, plus a critical backend bugfix for PostGIS geometry serialization.

## What Was Done

### Task 1: Rewrite client.ts — Real API Integration

Replaced all `mock-data.ts` imports with real `fetch()` calls to `http://localhost:8000/api/v1/`:

- **useStructuresGeoJSON**: `GET /structures?format=geojson&limit=1000` — maps API GeoJSON features to `StructureFeature` with proper type/condition mapping
- **useStructureDetail**: `GET /structures/{id}` — maps flat API response to `StructureDetail` with coordinates, admin location, technical specs
- **useInspections**: `GET /structures/{id}/inspections?limit=100` — maps inspection records with photos
- **useDocuments**: `GET /structures/{id}/documents` — maps document metadata with presigned URLs
- **useRiskScore**: `GET /structures/{id}/risk` — maps composite_score, contributing_factors to `RiskScore` with 4 components
- **useDiscoveryCandidates**: `GET /candidates?limit=1000` — maps candidate records
- **useMatchResults**: Derived from candidate match_status/confidence_score
- **useDiscoveryCandidate**: `GET /candidates/{id}`
- **useMatchResult**: `GET /candidates/{id}` — extracts match data
- **mockSubmitReviewAction**: `POST /candidates/{id}/review` — async, falls back to local record on failure
- **useOverrides**: Returns empty array (no GET endpoint exists yet)

Auth: Bearer token obtained via `POST /auth/token` with `dev-admin-key`, cached in module scope, auto-refreshed on 401.

Error handling: All fetch failures return empty collections or null so the UI degrades gracefully.

### Task 2: Rewrite chat-store.ts — Real Copilot API

Replaced `mockAIEngine()` with real `POST /api/v1/copilot/chat`:

- Sends `{message, conversation_id, context: {locale}}` to backend
- Maps `evidence` items to `CopilotSource[]` (source_type → CopilotSourceType)
- Stores `conversation_id` for multi-turn continuity
- Preserves word-by-word streaming animation using real response text
- Error fallback message in user's locale (ru/kk/en)
- Removed `mockAIEngine` import entirely

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed WKBElement geometry serialization in StructureResponse**
- **Found during:** Task 1 (testing structures endpoint)
- **Issue:** `GET /api/v1/structures` returned HTTP 500 — Pydantic couldn't serialize GeoAlchemy2 `WKBElement` (PostGIS EWKB binary) to `dict`
- **Fix:** Added `field_validator('geometry', mode='before')` to `StructureResponse` that parses EWKB to GeoJSON dict using `struct.unpack` (no shapely dependency needed)
- **Files modified:** `apps/api/src/api/schemas/structures.py`
- **Commit:** `4b14923`

## Verification

- `npx tsc --noEmit` — passes with zero errors
- `GET /api/v1/structures?format=geojson` — returns 230 features with Point geometry
- `POST /api/v1/copilot/chat` — returns message, evidence, suggestions, conversation_id
- `GET /api/v1/structures/{id}/risk` — returns composite_score, repair_status, inspection_interval
- No imports from `mock-data.ts` or `mock-ai-engine.ts` in target files
- Auth token included in all API calls via `Authorization: Bearer` header

## Commits

- `4b14923`: fix: WKBElement geometry serialization in StructureResponse
- `b02a655`: feat: replace all mock data with real backend API calls

## Known Stubs

- `useOverrides`: Returns empty array — backend has POST /structures/{id}/override but no GET endpoint to list existing overrides
- `useMatchResults`/`useMatchResult`: Match evidence array is empty — backend returns evidence as a dict, not the typed `MatchEvidence[]` array the frontend expects. Score and status work correctly.
- Other files still importing from `mock-data.ts` directly (filter-panel.tsx, document-upload.tsx, export-panel.tsx, field-inspection-form.tsx) — out of scope for this task
- `suggested-prompts.tsx` still imports `getSuggestedPrompts` from `mock-ai-engine.ts` — out of scope but functional (static prompt suggestions don't need API)

## Self-Check: PASSED

- `apps/web/lib/api/client.ts` — FOUND (modified, no mock imports)
- `apps/web/lib/stores/chat-store.ts` — FOUND (modified, no mock imports)
- `apps/api/src/api/schemas/structures.py` — FOUND (modified, validator added)
- Commit `4b14923` — FOUND in git log
- Commit `b02a655` — FOUND in git log
- `npx tsc --noEmit` — PASSED (zero errors)
