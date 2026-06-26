# Phase 4 Research: Discovery & Matching UI

## Requirements
- **DISC-04**: User can review candidate matches in a human-in-the-loop workflow showing existing record vs candidate with evidence chips (name similarity, distance, type agreement, source evidence)
- **UI-03**: UI displays confidence badges and provenance source chips on all AI-inferred and externally-sourced attributes

## Architecture

### Route
- `/hydrofinder` — already exists as placeholder page in `app/[locale]/hydrofinder/page.tsx`
- Page is async Server Component using `getTranslations()` and `setRequestLocale()`
- Delegates to client components

### Data Flow
- Mock data in `lib/api/mock-data.ts` (no backend)
- TanStack Query hooks in `lib/api/client.ts`
- Zustand store for discovery state in `lib/stores/discovery-store.ts`
- Types in `lib/api/types.ts`

### Component Structure
```
components/discovery/
  confidence-badge.tsx    — HIGH/MEDIUM/LOW badge with color
  source-chip.tsx         — provenance source chip (OSM, satellite, kazvodhoz)
  evidence-chip.tsx       — evidence chip (name similarity, distance, type agreement)
  candidate-list.tsx      — table of candidates with confidence + source
  comparison-view.tsx     — side-by-side existing vs candidate
  review-actions.tsx      — accept/link/reject buttons
  discovery-view.tsx      — orchestrates everything (client component)
```

### i18n
- New namespace `discovery` in messages/{en,ru,kk}.json
- All UI text trilingual

### Existing Patterns to Follow
- Pages: async Server Component → delegate to client component
- Client components: `useTranslations()`, `useQuery()` hooks
- shadcn/ui: Card, Badge, Button, Table, Tabs, Separator, ScrollArea
- Zustand stores: `create<State>()((set) => ({...}))`
- API hooks: `useQuery({ queryKey: [...], queryFn: ... })`

## Assumptions
1. No new packages needed — all required shadcn/ui components already exist
2. Mock data simulates discovery pipeline results (OSM candidates, satellite candidates)
3. Review actions are client-side state changes (no actual backend mutations)
4. Permission gating: admin and engineer can review candidates
5. The `/hydrofinder` route is the correct place for this feature

## Pitfalls
- next-intl: use `useTranslations()` in client components, `getTranslations()` in server components
- Async Server Components cannot use `useTranslations()` hook
- Zustand persist middleware for auth, simple create for others
- Ensure i18n keys are added to ALL THREE message files (en, ru, kk)
- Lucide icons already in deps — use for UI icons
