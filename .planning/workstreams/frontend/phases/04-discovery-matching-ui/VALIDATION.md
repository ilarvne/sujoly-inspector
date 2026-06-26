# Phase 4 Validation: Discovery & Matching UI

## Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| DISC-04 | ✅ Complete | Candidate list, side-by-side comparison with evidence chips, review workflow (accept/link/reject) |
| UI-03 | ✅ Complete | ConfidenceBadge (HIGH/MEDIUM/LOW), SourceChip (OSM/satellite/kazvodhoz), EvidenceChip (name similarity, distance, type agreement, source overlap) |

## Success Criteria

1. ✅ **Candidate list view showing found objects with confidence scores and source evidence**
   - `CandidateList` component with table showing source, name, type, confidence, match score, status
   - Confidence badges and source chips on each row

2. ✅ **Side-by-side comparison: existing record vs candidate with evidence chips**
   - `ComparisonView` component showing existing vs candidate side-by-side
   - Evidence chips: name similarity, distance, type agreement, source overlap
   - Match score progress bar

3. ✅ **Review workflow: accept (add to registry), link (merge), reject (false positive) with one-click actions**
   - `ReviewActions` component with three buttons
   - Confirmation dialog with optional reason field
   - Permission guard (admin/engineer only)

4. ✅ **Confidence badges (HIGH/MEDIUM/LOW) and provenance source chips visible throughout UI**
   - `ConfidenceBadge` used in candidate list and comparison view
   - `SourceChip` used in candidate list and comparison view

## Build Status
- `npm run build` passes — 36 routes prerendered successfully

## Files Created
- `lib/api/types.ts` — Discovery types (DiscoveryCandidate, MatchResult, MatchEvidence, etc.)
- `lib/api/mock-data.ts` — 20 mock candidates, match results, review submission
- `lib/api/client.ts` — TanStack Query hooks (useDiscoveryCandidates, useMatchResults, etc.)
- `lib/stores/discovery-store.ts` — Zustand store for discovery state
- `components/discovery/confidence-badge.tsx` — Reusable confidence badge
- `components/discovery/source-chip.tsx` — Reusable source chip
- `components/discovery/evidence-chip.tsx` — Reusable evidence chip
- `components/discovery/candidate-list.tsx` — Candidate table with filters
- `components/discovery/comparison-view.tsx` — Side-by-side comparison
- `components/discovery/review-actions.tsx` — Review workflow actions
- `components/discovery/discovery-view.tsx` — Main orchestration component
- `app/[locale]/hydrofinder/page.tsx` — Updated page wiring

## i18n
- `discovery` namespace added to en.json, ru.json, kk.json
- All UI text trilingual
