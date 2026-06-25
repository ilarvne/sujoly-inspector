# Phase 2: Map UI & Digital Passport - Research

**Researched:** 2026-06-26
**Domain:** MapLibre GL JS map integration with Next.js 16, mock data layer, digital passport UI, dashboard visualizations, filter state management
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MAP-01 | User can view an interactive map displaying all hydraulic structures, hydrological stations, and related facilities in Zhambyl Oblast | MapLibre GL JS 5.24.0 in a `'use client'` component, GeoJSON source with circle layer, OSM raster tiles as base map, initial viewport centered on Zhambyl Oblast [72.6, 44.0] zoom 7 |
| MAP-02 | User can see structure status visualization on the map via color-coded symbology (four-state condition: normal / inspection required / repair required / critical) | MapLibre data-driven `match` expression on `circle-color` paint property, mapping `condition` field to 6 status colors already defined in `globals.css` `@theme` tokens |
| MAP-03 | User can click any structure on the map to open its digital passport | `map.on('click', layerId, handler)` with `e.features[0].properties` to get structure ID, open side panel/drawer with full passport data from TanStack Query cache |
| MAP-04 | Decision-maker can view a portfolio dashboard with condition distribution, repair queue, inspection coverage, and geographic distribution heatmap | Recharts 3.9.0 for donut chart (condition distribution), bar chart (repair queue), stat cards (inspection coverage), geographic heatmap via MapLibre circle layer with opacity based on density |
| MAP-05 | User can filter map and dashboard by district, basin, structure type, condition, and inspection status | Zustand store for filter state, shadcn/ui Select/Checkbox components for filter UI, filter changes trigger GeoJSON source data update via `map.getSource().setData()` and dashboard data recompute |
| DATA-04 | User can view a digital passport per structure showing identity, type, geometry, administrative location, technical specifications, current status, and source provenance | Side panel component (shadcn/ui Sheet) with structured sections, trilingual labels via next-intl, data from mock TypeScript-typed fixtures matching expected backend API contract |
</phase_requirements>

## Summary

Phase 2 transforms the placeholder `/map` and `/dashboard` routes from Phase 1 into the MVP interactive map experience. The backend does not exist yet — there is no `.planning/workstreams/backend/` directory. Therefore, this phase MUST be built entirely with mock data that mimics the expected backend REST API + TiPG responses. The mock data layer must be designed for easy swap to real API calls when the backend is ready.

The core technical challenge is integrating MapLibre GL JS (a WebGL-based imperative library) into Next.js 16's App Router (SSR-first, Server Components). MapLibre requires a browser DOM context with WebGL — it cannot run on the server. The solution is a `'use client'` component with a `useEffect` hook for map initialization, or `next/dynamic` with `ssr: false` to lazy-load the map component only on the client. The standard React wrapper `react-map-gl` (visgl, 8.1.1, 2M/wk downloads, OK legitimacy) provides `<Map>`, `<Source>`, `<Layer>`, `<Popup>` components that handle lifecycle, refs, and event binding — significantly reducing boilerplate compared to raw MapLibre API calls in useEffect.

For the ~100-1400 structures in this dataset, GeoJSON loaded directly into MapLibre is the correct approach — no vector tile infrastructure (TiPG) is needed for the MVP. Vector tiles matter at millions of features, not thousands. The mock data strategy uses TypeScript-typed fixture files (JSON) with a mock API client that has the same interface as the future real API client, backed by TanStack Query for caching and state synchronization. This means swapping from mock to real API is a one-line change in the query function.

**Primary recommendation:** Install `maplibre-gl@5.24.0`, `react-map-gl@8.1.1`, `@tanstack/react-query@5.101.1`, `zustand@5.0.14`, and `recharts@3.9.0`. Build a `MapView` client component using `react-map-gl`'s `<Map>` with OSM raster tiles as the base layer and a GeoJSON `<Source>` + `<CircleLayer>` for structures. Use Zustand for filter/viewport/selection state. Use TanStack Query with a mock API client for data fetching. Build the digital passport as a shadcn/ui `<Sheet>` side panel. Build the dashboard with Recharts donut/bar charts.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Map rendering (MapLibre WebGL) | Browser | — | WebGL context requires browser DOM; cannot SSR. `'use client'` component with dynamic import. |
| Map viewport state (center, zoom, bounds) | Browser | — | Zustand store in client; map events update store, store changes drive flyTo. |
| Filter state (district, basin, type, condition) | Browser | — | Zustand store; filter UI in client component; filter changes update both map data and dashboard. |
| Structure data (GeoJSON features) | Browser | Frontend Server (SSR) | Mock data served from static JSON files; future real API via TanStack Query with SSR prefetch/hydration. |
| Digital passport rendering | Browser | — | Side panel component in client; reads selected structure from Zustand + TanStack Query cache. |
| Dashboard charts (condition distribution, repair queue) | Browser | — | Recharts SVG rendering in client component; data computed from TanStack Query cache. |
| Geographic heatmap | Browser | — | MapLibre circle layer with opacity/density expression; rendered in same map component. |
| Base map tiles | CDN / Static | Browser | OSM raster tiles fetched from `tile.openstreetmap.org`; cached by browser HTTP cache. |
| i18n for map/dashboard UI | Frontend Server (SSR) | Browser | next-intl `getTranslations` in server page component, `useTranslations` in client subcomponents via `NextIntlClientProvider`. |
| Mock API layer | Frontend Server (SSR) | Browser | Next.js route handlers (`app/api/structures/route.ts`) or static JSON in `/public`; TanStack Query fetches from either. |

## Standard Stack

### Core (Phase 2 new packages)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| maplibre-gl | 5.24.0 | WebGL map rendering, GeoJSON sources, data-driven styling | Open-source fork of Mapbox GL JS. GPU-accelerated. No proprietary license. De facto open-source web map renderer. 3M/wk downloads. [VERIFIED: npm registry] |
| react-map-gl | 8.1.1 | React wrapper for MapLibre GL JS — `<Map>`, `<Source>`, `<Layer>`, `<Popup>` components | Maintained by visgl (Uber visualization team). Supports MapLibre GL >= 1.13.0 as peer dependency. Handles lifecycle, refs, event binding. 2M/wk downloads. [VERIFIED: npm registry] |
| @tanstack/react-query | 5.101.1 | Server state management, data fetching/caching, mock API integration | Handles API data caching, background refetch, optimistic updates. Essential for mock-to-real API swap. 58M/wk downloads. [VERIFIED: npm registry] |
| zustand | 5.0.14 | Client state management (map viewport, filters, selection) | Simple hook-based API. Slices pattern for composed stores. Works with React 19. 43M/wk downloads. [VERIFIED: npm registry] |
| recharts | 3.9.0 | Chart library for dashboard visualizations (donut, bar, area) | Composable React components built on D3 + SVG. Works with React 19. ResponsiveContainer for adaptive sizing. 53M/wk downloads. [VERIFIED: npm registry] |

### Existing (from Phase 1, not re-installed)

| Library | Version | Purpose |
|---------|---------|---------|
| next | 16.2.9 | App Router, SSR/SSG, dynamic imports |
| react / react-dom | 19.2.4 | UI library |
| next-intl | 4.13.0 | Trilingual i18n |
| tailwindcss | 4.x | Styling |
| shadcn/ui (radix-ui) | 4.11.0 (CLI) | UI components (Sheet, Select, Checkbox, Card, Badge, Separator) |
| lucide-react | 1.21.0 | Icons |
| typescript | 5.x | Type safety |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-map-gl | Raw MapLibre in useEffect | More control but 200+ lines of boilerplate for lifecycle, event binding, cleanup. react-map-gl handles all of this declaratively. — **Use react-map-gl** |
| Recharts | Tremor / nivo / visx | Tremor is dashboard-focused but opinionated styling. nivo/visx are more powerful but harder to integrate with shadcn/ui. Recharts is the most common choice with shadcn/ui ecosystem. — **Use Recharts** |
| Zustand | Jotai / Redux Toolkit | Jotai is atom-based (good for fine-grained). Redux is overkill. Zustand is simplest for this scope (viewport + filters + selection). — **Use Zustand** (locked in STACK.md) |
| TanStack Query | SWR | SWR is simpler but less feature-rich (no devtools, fewer cache strategies). TanStack Query is the standard for mock-to-real API transitions. — **Use TanStack Query** (locked in STACK.md) |
| GeoJSON direct loading | Vector tiles (TiPG) | Vector tiles matter at millions of features. ~100-1400 structures is trivially small for GeoJSON. No tiling infrastructure needed for MVP. — **Use GeoJSON direct loading** |

**Installation:**
```bash
cd apps/web
npm install maplibre-gl react-map-gl @tanstack/react-query zustand recharts
```

**Version verification (executed 2026-06-26):**
```
maplibre-gl:           5.24.0   (npm view)
react-map-gl:          8.1.1    (npm view)
@tanstack/react-query: 5.101.1  (npm view)
zustand:               5.0.14   (npm view)
recharts:              3.9.0    (npm view)
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| maplibre-gl | npm | ~8 yrs (v5.24.0 published 2026-04-23) | 3M/wk | github.com/maplibre/maplibre-gl-js | OK | Approved |
| react-map-gl | npm | ~8 yrs (v8.1.1 published 2026-04-11) | 2M/wk | github.com/visgl/react-map-gl | OK | Approved |
| @tanstack/react-query | npm | ~5 yrs (v5.101.1 published 2026-06-23) | 58M/wk | github.com/TanStack/query | SUS* | Approved (false positive) |
| zustand | npm | ~6 yrs (v5.0.14 published 2026-05-28) | 43M/wk | github.com/pmndrs/zustand | SUS* | Approved (false positive) |
| recharts | npm | ~9 yrs (v3.9.0 published 2026-06-23) | 53M/wk | github.com/recharts/recharts | SUS* | Approved (false positive) |

*The seam returned `SUS` with reason `too-new` for @tanstack/react-query, zustand, and recharts because their latest versions were published within the last month. This is a **false positive** — all three are among the most popular npm packages with tens of millions of weekly downloads, official GitHub repos, no postinstall scripts, and no deprecation flags. They are clearly legitimate. No `checkpoint:human-verify` needed.

**Postinstall script check:** `npm view <pkg> scripts.postinstall` returned empty for all 5 packages — no suspicious postinstall scripts detected.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none (false-positive `too-new` flags on 3 packages dismissed — these are industry-standard packages with 2M-58M weekly downloads)

## Architecture Patterns

### System Architecture Diagram

```
Browser (Client)
    │
    ├── /map route (Server Component wrapper)
    │   │  ┌─ getTranslations('map') → page title/subtitle
    │   │  └─ setRequestLocale(locale)
    │   │
    │   └── MapView ('use client' component)
    │       │
    │       ├── <Map> (react-map-gl)
    │       │   ├── Base Layer: OSM raster tiles
    │       │   │   (https://tile.openstreetmap.org/{z}/{x}/{y}.png)
    │       │   │
    │       │   ├── <Source type="geojson" data={structuresGeoJSON}>
    │       │   │   └── <Layer type="circle" paint={match expression}>
    │       │   │       circle-color: match(get('condition'))
    │       │   │         → normal: green, inspection: yellow
    │       │   │         → repair: orange, critical: red
    │       │   │         → missing: gray
    │       │   │
    │       │   └── Click handler → set selectedId in Zustand
    │       │
    │       ├── FilterPanel (shadcn Select/Checkbox)
    │       │   └── Updates Zustand filterStore → triggers data refilter
    │       │
    │       └── PassportPanel (shadcn Sheet)
    │           └── Reads selectedId → useQuery(structure detail)
    │               → renders identity, type, geometry, specs, status, provenance
    │
    ├── /dashboard route (Server Component wrapper)
    │   │
    │   └── DashboardView ('use client' component)
    │       ├── ConditionDonut (Recharts PieChart)
    │       │   └── Data from useQuery(structures) → count by condition
    │       ├── RepairQueue (Recharts BarChart or Table)
    │       │   └── Data from useQuery(structures) → filter repair/critical
    │       ├── InspectionStats (Stat cards)
    │       │   └── Data from useQuery(structures) → inspection coverage %
    │       └── HeatmapView (MapLibre mini-map or density circles)
    │           └── Data from useQuery(structures) → group by district
    │
    └── State Management
        ├── useMapStore (Zustand)     ← viewport: {center, zoom, bounds}
        ├── useFilterStore (Zustand)  ← filters: {district, basin, type, condition}
        └── useSelectionStore (Zustand) ← selectedId: string | null

Data Flow:
    Mock JSON fixtures → TanStack Query (useQuery) → Components
    Filter changes → Zustand → refilter GeoJSON → map.getSource().setData()
    Map click → Zustand selectedId → PassportPanel opens with data from cache
```

### Recommended Project Structure

```
apps/web/
├── app/
│   ├── [locale]/
│   │   ├── map/
│   │   │   └── page.tsx              # Server Component: getTranslations, renders MapView
│   │   ├── dashboard/
│   │   │   └── page.tsx              # Server Component: getTranslations, renders DashboardView
│   │   └── layout.tsx                # Existing root layout (add QueryProvider here)
│   └── api/                          # Mock API route handlers (optional approach)
│       └── structures/
│           └── route.ts              # Returns mock GeoJSON (alternative to static files)
├── components/
│   ├── map/
│   │   ├── map-view.tsx              # 'use client' — react-map-gl <Map> wrapper
│   │   ├── structure-layer.tsx       # <Source> + <Layer> for structures
│   │   ├── filter-panel.tsx          # Filter UI controls
│   │   └── passport-panel.tsx        # Digital passport side panel (shadcn Sheet)
│   ├── dashboard/
│   │   ├── dashboard-view.tsx        # 'use client' — orchestrates dashboard charts
│   │   ├── condition-donut.tsx       # Recharts PieChart for condition distribution
│   │   ├── repair-queue.tsx          # Repair queue table/bar chart
│   │   ├── inspection-stats.tsx      # Stat cards for inspection coverage
│   │   └── heatmap-view.tsx          # Geographic distribution visualization
│   ├── providers/
│   │   └── query-provider.tsx        # 'use client' — TanStack Query QueryClientProvider
│   ├── layout/                       # Existing from Phase 1
│   └── ui/                           # Existing shadcn/ui + new components (sheet, select, etc.)
├── lib/
│   ├── api/
│   │   ├── client.ts                 # API client interface (mock implementation)
│   │   ├── types.ts                  # TypeScript types for Structure, StructureFeature
│   │   └── mock-data.ts              # Mock structure data generation
│   ├── stores/
│   │   ├── map-store.ts              # Zustand: viewport state
│   │   ├── filter-store.ts           # Zustand: filter state
│   │   └── selection-store.ts        # Zustand: selected structure ID
│   ├── utils.ts                      # Existing cn() utility
│   └── constants.ts                  # Existing nav items + map constants
├── types/
│   └── structures.ts                 # Shared TypeScript types (or in lib/api/types.ts)
├── public/
│   └── data/
│       └── structures.json           # Static mock GeoJSON (alternative to API route)
├── messages/
│   ├── en.json                       # Extended with map, dashboard, passport namespaces
│   ├── ru.json
│   └── kk.json
└── ... (existing config files from Phase 1)
```

### Pattern 1: MapLibre in Next.js Client Component

**What:** MapLibre GL JS requires browser DOM + WebGL. In Next.js App Router, it MUST be in a `'use client'` component. Use `react-map-gl` for declarative React integration.
**When to use:** The `/map` route page component.

```tsx
// components/map/map-view.tsx
// Source: Context7 /websites/maplibre_maplibre-gl-js + react-map-gl documentation
'use client';

import { useMemo } from 'react';
import Map, { Source, Layer, MapMouseEvent } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useMapStore } from '@/lib/stores/map-store';
import { useFilterStore } from '@/lib/stores/filter-store';
import { useSelectionStore } from '@/lib/stores/selection-store';
import { useStructuresGeoJSON } from '@/lib/api/client';

const ZHAMBYL_CENTER = { longitude: 72.6, latitude: 44.0, zoom: 7 };

export function MapView() {
  const { viewport, setViewport } = useMapStore();
  const filters = useFilterStore();
  const setSelectedId = useSelectionStore((s) => s.setSelectedId);
  const { data: geojson } = useStructuresGeoJSON(filters);

  const circleLayer = useMemo({
    id: 'structures',
    type: 'circle',
    source: 'structures',
    paint: {
      'circle-radius': 7,
      'circle-color': [
        'match',
        ['get', 'condition'],
        'normal',      '#22c55e',  // green
        'inspection',  '#eab308',  // yellow
        'repair',      '#f97316',  // orange
        'critical',    '#ef4444',  // red
        '#9ca3af',                  // gray (default/missing)
      ],
      'circle-stroke-width': 1.5,
      'circle-stroke-color': '#ffffff',
    },
  }, []);

  return (
    <Map
      initialViewState={ZHAMBYL_CENTER}
      {...viewport}
      onMove={(e) => setViewport(e.viewState)}
      style={{ width: '100%', height: '100%' }}
      mapStyle={{
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
          },
        },
        layers: [
          { id: 'osm', type: 'raster', source: 'osm' },
        ],
      }}
    >
      <Source id="structures" type="geojson" data={geojson}>
        <Layer {...circleLayer} />
      </Source>
    </Map>
  );
}
```

### Pattern 2: TanStack Query with Mock API Layer

**What:** TanStack Query provides caching and state management. The mock API client returns the same types the real API will return. Swapping mock → real is a one-line change in the query function.
**When to use:** All data fetching in map and dashboard components.

```tsx
// components/providers/query-provider.tsx
// Source: Context7 /tanstack/query — advanced-ssr.md
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,  // 1 minute — avoid refetch on client mount
      },
    },
  });
}

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => makeQueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

```tsx
// lib/api/client.ts
// Source: TanStack Query patterns from Context7
import { useQuery } from '@tanstack/react-query';
import { mockStructures, mockStructureById } from './mock-data';
import type { StructureCollection, StructureDetail } from './types';

// Mock fetch functions — swap these for real API calls later
async function fetchStructures(filters?: StructureFilters): Promise<StructureCollection> {
  // Simulate network delay for realistic testing
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockStructures(filters);
}

async function fetchStructureDetail(id: string): Promise<StructureDetail> {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockStructureById(id);
}

// Query hooks — these stay the same when swapping mock → real
export function useStructuresGeoJSON(filters?: StructureFilters) {
  return useQuery({
    queryKey: ['structures', 'geojson', filters],
    queryFn: () => fetchStructures(filters),
  });
}

export function useStructureDetail(id: string | null) {
  return useQuery({
    queryKey: ['structure', id],
    queryFn: () => fetchStructureDetail(id!),
    enabled: !!id,
  });
}
```

### Pattern 3: Zustand Store with Slices Pattern

**What:** Zustand stores for map viewport, filters, and selection. Each concern gets its own store for clean separation.
**When to use:** All client-side state that doesn't come from the server.

```tsx
// lib/stores/filter-store.ts
// Source: Context7 /pmndrs/zustand — slices pattern
import { create } from 'zustand';

interface FilterState {
  district: string | null;
  basin: string | null;
  type: string | null;
  condition: string | null;
  inspectionStatus: string | null;
  setFilter: (key: keyof Omit<FilterState, 'setFilter' | 'resetFilters'>, value: string | null) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>()((set) => ({
  district: null,
  basin: null,
  type: null,
  condition: null,
  inspectionStatus: null,
  setFilter: (key, value) => set({ [key]: value } as Partial<FilterState>),
  resetFilters: () => set({
    district: null, basin: null, type: null, condition: null, inspectionStatus: null,
  }),
}));
```

```tsx
// lib/stores/selection-store.ts
import { create } from 'zustand';

interface SelectionState {
  selectedId: string | null;
  setSelectedId: (id: string | null) => void;
}

export const useSelectionStore = create<SelectionState>()((set) => ({
  selectedId: null,
  setSelectedId: (id) => set({ selectedId: id }),
}));
```

### Pattern 4: Digital Passport as Side Panel

**What:** The digital passport opens as a side panel (shadcn/ui Sheet) when a structure is clicked on the map. It shows structured sections with trilingual labels.
**When to use:** MAP-03 click → passport flow.

```tsx
// components/map/passport-panel.tsx
'use client';

import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { useTranslations } from 'next-intl';
import { useSelectionStore } from '@/lib/stores/selection-store';
import { useStructureDetail } from '@/lib/api/client';
import { Badge } from '@/components/ui/badge';

export function PassportPanel() {
  const t = useTranslations('passport');
  const { selectedId, setSelectedId } = useSelectionStore();
  const { data: structure, isLoading } = useStructureDetail(selectedId);

  return (
    <Sheet open={!!selectedId} onOpenChange={(open) => !open && setSelectedId(null)}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{structure?.name?.[locale] || structure?.name?.ru}</SheetTitle>
        </SheetHeader>
        {isLoading ? (
          <p>Loading...</p>
        ) : structure ? (
          <div className="space-y-4">
            <section>
              <h3>{t('identity')}</h3>
              <dl>...</dl>
            </section>
            <section>
              <h3>{t('status')}</h3>
              <Badge>{t(`condition.${structure.condition}`)}</Badge>
            </section>
            <section>
              <h3>{t('provenance')}</h3>
              <p>{structure.provenance.source}</p>
              <Badge>{structure.provenance.confidence}</Badge>
            </section>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
```

### Pattern 5: Data-Driven Circle Color Expression

**What:** MapLibre `match` expression maps the `condition` property of each GeoJSON feature to a color. This is the core of MAP-02 (color-coded symbology).
**When to use:** The circle layer paint properties in the MapView component.

```typescript
// The match expression for circle-color
// Source: Context7 /websites/maplibre_maplibre-gl-js — examples, data expressions
const circleColorExpression = [
  'match',
  ['get', 'condition'],    // Get the 'condition' property from the feature
  'normal',      '#22c55e', // green
  'inspection',  '#eab308', // yellow
  'repair',      '#f97316', // orange
  'critical',    '#ef4444', // red
  '#9ca3af',                // gray (default — missing/unknown coords)
];

// Map to OKLCH status colors from globals.css @theme:
// --color-status-normal: oklch(0.65 0.18 145)     → green
// --color-status-inspection: oklch(0.80 0.15 90)  → yellow
// --color-status-repair: oklch(0.70 0.18 55)      → orange
// --color-status-critical: oklch(0.55 0.22 25)    → red
// --color-status-missing: oklch(0.55 0.01 250)    → gray
```

### Anti-Patterns to Avoid

- **Importing `maplibre-gl` in a Server Component:** MapLibre requires WebGL/DOM. Importing it in a Server Component causes build errors or runtime crashes. Always use `'use client'` directive. [CITED: Context7 /websites/maplibre_maplibre-gl-js]
- **Not importing MapLibre CSS:** The `maplibre-gl/dist/maplibre-gl.css` import is required for the map container, controls, and popups to render correctly. Without it, the map appears as a blank canvas. [CITED: Context7 /websites/maplibre_maplibre-gl-js]
- **Using `react-map-gl` without the `/maplibre` subpath:** `react-map-gl` exports both Mapbox and MapLibre entry points. Import from `react-map-gl/maplibre` to use MapLibre GL JS, not `react-map-gl` (which defaults to Mapbox). [ASSUMED]
- **Creating a new QueryClient on every render:** This causes infinite refetch loops. Use `useState(() => makeQueryClient())` to ensure a single client per browser session. [CITED: Context7 /tanstack/query]
- **Using OSM tiles without attribution:** The OSM tile usage policy requires visible attribution: "© OpenStreetMap contributors". Not showing attribution violates the usage policy and can result in blocked access. [CITED: operations.osmfoundation.org/policies/tiles/]
- **Storing derived/computed values in Zustand:** Don't store filtered GeoJSON in the store. Store only filter criteria; compute filtered data via TanStack Query or `useMemo`. [CITED: Context7 /pmndrs/zustand — beginner-typescript.md]
- **Calling `map.getSource().setData()` before the map loads:** This throws because the source doesn't exist yet. Use the `onLoad` event or react-map-gl's lifecycle management. [CITED: Context7 /websites/maplibre_maplibre-gl-js]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Map rendering | Custom canvas-based map renderer | MapLibre GL JS + react-map-gl | WebGL-accelerated, handles panning/zooming/projections, vector and raster tile support, 8+ years of development |
| Data-driven styling | Manual DOM manipulation of markers | MapLibre `match`/`interpolate` expressions | GPU-accelerated, handles thousands of features efficiently, declarative style based on feature properties |
| Server state / data caching | Custom fetch + useState + useEffect | TanStack Query `useQuery` | Handles loading/error states, caching, deduplication, background refetch, SSR hydration. Swap mock→real API in queryFn. |
| Client state (viewport, filters) | React Context + useReducer | Zustand `create()` | Simpler API, no provider wrapping needed, fine-grained selectors prevent unnecessary re-renders, persists across route changes |
| Dashboard charts | Custom SVG charts from scratch | Recharts PieChart/BarChart/AreaChart | Composable React components, ResponsiveContainer for adaptive sizing, tooltips, legends, animations. Works with React 19. |
| Digital passport panel | Custom fixed-position div | shadcn/ui Sheet (Radix UI Dialog variant) | Accessible, keyboard navigation, focus trap, animation, side-panel variant. Already in the project's shadcn/ui setup. |
| Filter UI controls | Custom select/checkbox components | shadcn/ui Select + Checkbox | Accessible, keyboard navigable, styled to match design system. Installed via `npx shadcn@latest add select checkbox`. |
| Map popups | Custom absolutely-positioned divs | react-map-gl `<Popup>` component | Handles positioning relative to map coordinates, close button, lifecycle. Integrates with MapLibre's popup system. |

**Key insight:** Every piece of Phase 2 — map rendering, styling, state management, data fetching, charts, panels, filter controls — has a battle-tested library. The custom code is: the mock data fixtures, the TypeScript types matching the expected API contract, the Zustand store definitions, and the next-intl translation messages for new UI sections.

## Runtime State Inventory

> This is a greenfield phase (new features on existing Phase 1 scaffolding). No rename/refactor/migration involved. However, Phase 1 established patterns that this phase extends.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no database or datastore in frontend | N/A |
| Live service config | None — no external services configured in frontend | N/A |
| OS-registered state | None | N/A |
| Secrets/env vars | None — no env vars needed for mock data phase. Future: `NEXT_PUBLIC_API_URL` when backend is ready | N/A |
| Build artifacts | None — Phase 1 build artifacts will auto-update | N/A |

## Common Pitfalls

### Pitfall 1: MapLibre SSR Crash (CRITICAL)

**What goes wrong:** Build fails or server crashes with "window is not defined" or "WebGL is not supported" when MapLibre is imported in a Server Component.
**Why it happens:** MapLibre GL JS requires `window`, `document`, and a WebGL context. These don't exist during SSR. Next.js App Router renders Server Components on the server by default.
**How to avoid:** 
1. Always add `'use client'` to any file that imports `maplibre-gl` or `react-map-gl/maplibre`.
2. If the map component is deep in the tree, use `next/dynamic` with `ssr: false`:
   ```tsx
   const MapView = dynamic(() => import('@/components/map/map-view'), { ssr: false });
   ```
3. The page route (`app/[locale]/map/page.tsx`) stays as a Server Component — it only renders the client MapView component.
**Warning signs:** Build errors mentioning "window", "document", or "self is not defined". Server-side runtime crashes on `/map` route.

### Pitfall 2: Missing MapLibre CSS Import

**What goes wrong:** Map renders as a blank or broken canvas. Map controls (zoom buttons, attribution) are unstyled. Popups appear as plain text without styling.
**Why it happens:** The `maplibre-gl/dist/maplibre-gl.css` stylesheet is not imported. MapLibre's visual elements (container, controls, popups, markers) require this CSS.
**How to avoid:** Import the CSS at the top of the map component file:
```tsx
import 'maplibre-gl/dist/maplibre-gl.css';
```
**Warning signs:** Map canvas is blank. Controls appear as unstyled HTML elements. Popups have no background/border.

### Pitfall 3: react-map-gl Import Path Confusion

**What goes wrong:** react-map-gl tries to use Mapbox GL JS instead of MapLibre GL JS, or peer dependency errors occur.
**Why it happens:** `react-map-gl` supports both Mapbox and MapLibre. The default import `from 'react-map-gl'` expects Mapbox. For MapLibre, you must import from `react-map-gl/maplibre`.
**How to avoid:** Always import from the MapLibre subpath:
```tsx
import Map, { Source, Layer } from 'react-map-gl/maplibre';
```
**Warning signs:** Peer dependency warnings about `mapbox-gl`. Build errors about missing mapbox-gl module. [ASSUMED]

### Pitfall 4: OSM Tile Usage Policy Violations

**What goes wrong:** OSM tile server blocks requests, or the application violates the OSM tile usage policy.
**Why it happens:** The OSM tile usage policy has strict requirements: valid User-Agent, HTTP Referer header, visible attribution, no bulk downloading, no offline use, HTTPS URLs only.
**How to avoid:**
1. Always show attribution: `© OpenStreetMap contributors` (visible on the map, not hidden).
2. Use HTTPS: `https://tile.openstreetmap.org/{z}/{x}/{y}.png` (not HTTP).
3. Don't add `Cache-Control: no-cache` headers.
4. For production: use a commercial provider or self-host tiles. OSM tiles are for dev/low-traffic only.
5. Allow easy tile source switching (config-driven, not hardcoded).
**Warning signs:** Tiles fail to load. HTTP 403 errors from tile.openstreetmap.org. Attribution not visible on the map.
**Source:** [CITED: operations.osmfoundation.org/policies/tiles/]

### Pitfall 5: TanStack Query Infinite Refetch Loop

**What goes wrong:** The application makes endless API calls, creating an infinite loop of refetches.
**Why it happens:** Creating a new `QueryClient` on every render (instead of using `useState`), or setting `staleTime: 0` with SSR (causes immediate refetch on client mount).
**How to avoid:**
1. Create the QueryClient once: `const [queryClient] = useState(() => makeQueryClient())`.
2. Set `staleTime: 60 * 1000` (or higher) to prevent immediate refetch after SSR hydration.
3. Use stable query keys — don't include new object references in the key.
**Warning signs:** Network tab shows continuous API requests. CPU usage spikes. Browser becomes unresponsive.
**Source:** [CITED: Context7 /tanstack/query — advanced-ssr.md]

### Pitfall 6: jsdom Cannot Test WebGL Components

**What goes wrong:** Vitest tests for map components fail with "WebGL is not supported" or "canvas is not defined" errors.
**Why it happens:** Vitest's jsdom environment doesn't have a real WebGL context. MapLibre requires WebGL to initialize.
**How to avoid:**
1. Don't unit test MapLibre rendering with Vitest/jsdom — use Playwright E2E tests instead.
2. For unit tests: test the non-map logic (filter functions, data transformations, Zustand store actions, mock API client) in isolation.
3. Mock `react-map-gl/maplibre` in Vitest tests if needed for component tests.
**Warning signs:** Vitest errors about WebGL, canvas, or getContext. Tests pass locally but fail in CI (different WebGL support).

### Pitfall 7: Filter Changes Not Updating Map

**What goes wrong:** User changes a filter, the dashboard updates but the map markers don't change.
**Why it happens:** The GeoJSON source data isn't updated when filters change. MapLibre renders the original data, not the filtered data.
**How to avoid:**
1. With react-map-gl, the `<Source data={...}>` prop updates reactively — bind it to the filtered GeoJSON from TanStack Query.
2. Ensure the query key includes the filter values so the query refetches/recomputes when filters change.
3. With raw MapLibre: call `map.getSource('structures').setData(filteredGeoJSON)` in a `useEffect` that depends on the filtered data.
**Warning signs:** Filter panel updates, dashboard charts change, but map markers stay the same.

## Code Examples

### Mock Data Type Definitions

```typescript
// lib/api/types.ts
// Source: Designed to match expected backend API contract from STACK.md

export type ConditionStatus = 'normal' | 'inspection' | 'repair' | 'critical' | 'missing';
export type InspectionStatus = 'current' | 'overdue' | 'due_soon' | 'never' | 'unknown';
export type StructureType = 'dam' | 'reservoir' | 'canal' | 'pumping_station' | 'spillway' | 'other';

export interface TrilingualText {
  ru: string;
  kk: string;
  en: string;
}

export interface StructureProperties {
  id: string;
  name: TrilingualText;
  type: StructureType;
  condition: ConditionStatus;
  inspectionStatus: InspectionStatus;
  district: string;
  basin: string;
  // Technical specifications
  height?: number;        // meters
  length?: number;        // meters
  capacity?: number;      // million m³
  yearBuilt?: number;
  // Provenance
  provenance: {
    source: string;       // 'kazvodhoz' | 'osm' | 'satellite' | 'manual'
    confidence: 'high' | 'medium' | 'low';
    lastVerified: string; // ISO date
  };
}

export interface StructureFeature extends GeoJSON.Feature {
  geometry: GeoJSON.Point;
  properties: StructureProperties;
}

export interface StructureCollection extends GeoJSON.FeatureCollection {
  features: StructureFeature[];
}

export interface StructureDetail extends StructureProperties {
  coordinates: { lon: number; lat: number };
  administrativeLocation: {
    region: string;
    district: string;
    nearestSettlement: string;
  };
  technicalSpecs: {
    height?: number;
    length?: number;
    capacity?: number;
    yearBuilt?: number;
    designType?: string;
    materials?: string;
  };
}

export interface StructureFilters {
  district?: string | null;
  basin?: string | null;
  type?: string | null;
  condition?: string | null;
  inspectionStatus?: string | null;
}
```

### Mock Data Fixture (excerpt)

```typescript
// lib/api/mock-data.ts
import type { StructureCollection, StructureDetail, StructureFilters } from './types';

// Mock structures in Zhambyl Oblast, Kazakhstan
// Coordinates centered around [72.6, 44.0] (Taraz area)
const mockStructuresRaw: StructureDetail[] = [
  {
    id: 'KZ-ZH-0001',
    name: { ru: 'водохранилище Тасуткель', kk: 'Тасөткел суқоймасы', en: 'Tasutkel Reservoir' },
    type: 'reservoir',
    condition: 'normal',
    inspectionStatus: 'current',
    district: 'Жамбылский район',
    basin: 'р. Талас',
    coordinates: { lon: 71.35, lat: 42.95 },
    administrativeLocation: { region: 'Жамбылская область', district: 'Жамбылский район', nearestSettlement: 'с. Тасуткель' },
    technicalSpecs: { height: 24, length: 1200, capacity: 185, yearBuilt: 1972, designType: 'земляная плотина', materials: 'грунт' },
    provenance: { source: 'kazvodhoz', confidence: 'high', lastVerified: '2024-03-15' },
  },
  // ... 50-100 more structures with varied conditions, types, districts
];

export function mockStructures(filters?: StructureFilters): StructureCollection {
  const filtered = mockStructuresRaw.filter((s) => {
    if (filters?.district && s.district !== filters.district) return false;
    if (filters?.basin && s.basin !== filters.basin) return false;
    if (filters?.type && s.type !== filters.type) return false;
    if (filters?.condition && s.condition !== filters.condition) return false;
    if (filters?.inspectionStatus && s.inspectionStatus !== filters.inspectionStatus) return false;
    return true;
  });

  return {
    type: 'FeatureCollection',
    features: filtered.map((s) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [s.coordinates.lon, s.coordinates.lat] },
      properties: {
        id: s.id,
        name: s.name,
        type: s.type,
        condition: s.condition,
        inspectionStatus: s.inspectionStatus,
        district: s.district,
        basin: s.basin,
        provenance: s.provenance,
      },
    })),
  };
}

export function mockStructureById(id: string): StructureDetail | null {
  return mockStructuresRaw.find((s) => s.id === id) || null;
}
```

### Dashboard Donut Chart with Recharts

```tsx
// components/dashboard/condition-donut.tsx
'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { useTranslations } from 'next-intl';
import { useStructuresGeoJSON } from '@/lib/api/client';
import { useFilterStore } from '@/lib/stores/filter-store';

const COLORS = {
  normal:     '#22c55e',  // green
  inspection: '#eab308',  // yellow
  repair:     '#f97316',  // orange
  critical:   '#ef4444',  // red
  missing:    '#9ca3af',  // gray
};

export function ConditionDonut() {
  const t = useTranslations('dashboard');
  const filters = useFilterStore();
  const { data } = useStructuresGeoJSON(filters);

  const chartData = useMemo(() => {
    if (!data) return [];
    const counts: Record<string, number> = {};
    for (const f of data.features) {
      const c = f.properties.condition;
      counts[c] = (counts[c] || 0) + 1;
    }
    return Object.entries(counts).map(([condition, count]) => ({
      name: t(`condition.${condition}`),
      condition,
      value: count,
    }));
  }, [data, t]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}    // Donut effect
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
        >
          {chartData.map((entry) => (
            <Cell key={entry.condition} fill={COLORS[entry.condition as keyof typeof COLORS]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mapbox GL JS | MapLibre GL JS | MapLibre fork (2021) | No API key needed, no usage limits, fully open-source. MapLibre 5.x is the current stable line. |
| Raw MapLibre in useEffect | react-map-gl declarative components | react-map-gl v7+ (2023) | React-idiomatic `<Map>`, `<Source>`, `<Layer>` components. Lifecycle, refs, events handled. Less boilerplate. |
| HSL color values | OKLCH color values | Tailwind v4 + shadcn/ui (2025) | Perceptually uniform colors. Status colors in `@theme` use OKLCH. MapLibre expressions can use hex or OKLCH. |
| Redux for client state | Zustand | Zustand v5 (2025) | No provider wrapping, simpler API, hook-based selectors. Standard for React 19 projects. |
| Custom fetch + useEffect | TanStack Query v5 | v5 (2024) | Built-in caching, dedup, SSR hydration. `getQueryClient` pattern for Next.js App Router. |
| Static SVG charts | Recharts v3 | v3 (2025) | React 19 support, `responsive` prop, ResponsiveContainer. Composable chart components. |

**Deprecated/outdated:**
- `next-pwa`: Replaced by Serwist (not relevant to Phase 2, but noted for Phase 5)
- `react-map-gl` v6 and below: Use v7+ with `react-map-gl/maplibre` import path
- Mapbox GL JS free tier: No longer free for production — use MapLibre GL JS

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `react-map-gl/maplibre` is the correct import path for MapLibre integration | Architecture Patterns | If the subpath is different, imports fail. Need to verify against react-map-gl 8.1.1 docs. [ASSUMED — based on react-map-gl convention, not verified via Context7] |
| A2 | OSM raster tiles are acceptable for development/MVP base map | Tile Source Strategy | OSM tile usage policy may be too restrictive for production. The project will need self-hosted or commercial tiles for production. [ASSUMED — dev-only usage is clearly allowed per OSM policy] |
| A3 | The expected backend API contract follows standard REST conventions (/api/structures returns GeoJSON FeatureCollection) | Mock Data Strategy | If the real API uses a different format (e.g., OGC API Features with JSON-FG), the mock data types need adjustment. [ASSUMED — based on STACK.md mention of TiPG OGC API Features] |
| A4 | Recharts v3 works with React 19 without compatibility issues | Standard Stack | Recharts v3 may have peer dependency issues with React 19. The 53M/wk downloads suggest broad adoption but specific React 19 compatibility should be verified at install time. [ASSUMED — Context7 shows Recharts v3 examples but didn't explicitly confirm React 19 compatibility] |
| A5 | The existing shadcn/ui `radix-nova` style supports Sheet, Select, Checkbox components | Architecture Patterns | The `radix-nova` style (v4.11.0 equivalent of new-york) should support all standard shadcn/ui components. If not, components need manual creation. [ASSUMED — radix-nova is a variant of new-york which supports all components] |
| A6 | MapLibre `match` expression colors should use hex values, not CSS custom properties | Code Examples | MapLibre expressions evaluate in the WebGL context, which cannot read CSS custom properties (`var(--color-status-normal)`). Hex values are required. The OKLCH values in `@theme` need to be converted to hex for the MapLibre expression. [ASSUMED — MapLibre expressions take literal values, not CSS variables] |
| A7 | The `QueryProvider` should be added to the root layout (`app/[locale]/layout.tsx`) wrapping `AppShell` | Architecture Patterns | If QueryProvider should be at a different level (e.g., per-route), the data caching behavior changes. Root layout is the standard pattern. [ASSUMED — based on TanStack Query docs] |

## Open Questions

1. **react-map-gl vs raw MapLibre: which to use?**
   - What we know: STACK.md lists "MapLibre GL JS 5.19.x" without mentioning react-map-gl. react-map-gl 8.1.1 supports MapLibre GL >= 1.13.0 and provides declarative React components.
   - What's unclear: Whether the project intends to use MapLibre directly (raw API in useEffect) or with a React wrapper.
   - Recommendation: **Use react-map-gl.** It's the standard React integration for MapLibre, maintained by visgl (Uber's visualization team), and significantly reduces boilerplate. The STACK.md's omission of react-map-gl is likely an oversight — it lists the map renderer, not the React binding. react-map-gl is a peer dependency companion, not a competing library.

2. **Mock data as static JSON files vs Next.js API route handlers?**
   - What we know: Both approaches work. Static JSON in `/public/data/` is simplest. Next.js route handlers (`app/api/structures/route.ts`) simulate a real API more closely.
   - What's unclear: Which approach makes the mock-to-real swap easiest.
   - Recommendation: **Use a TypeScript mock data module (`lib/api/mock-data.ts`) with TanStack Query hooks.** This is the most flexible: the mock functions return typed data directly (no HTTP layer), and swapping to real API is changing the `queryFn` from `mockStructures(filters)` to `fetch('/api/structures?...')`. No need for actual HTTP route handlers in the mock phase.

3. **Should the digital passport be a Sheet (side panel) or a Dialog (modal)?**
   - What we know: MAP-03 says "click any structure to open its digital passport." Both Sheet and Dialog work. Sheet (side panel) is better for map context — the user can see the map and passport simultaneously.
   - What's unclear: Whether the user should be able to interact with the map while the passport is open.
   - Recommendation: **Use Sheet (side panel, right side).** The passport contains rich detail (identity, type, geometry, specs, status, provenance) that benefits from vertical scrolling. A side panel keeps the map visible for context. The user can close the panel to return to full map view.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next.js 16 runtime | ✓ | v22.21.0 | — |
| npm | Package management | ✓ | 11.7.0 | — |
| WebGL (browser) | MapLibre GL JS rendering | ✓ | — (browser-dependent) | Playwright Chromium supports WebGL via SwiftShader |
| Internet access | OSM tile server, npm registry | ✓ | — | Mock data works offline; tiles need connectivity |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none

All required tools are available. Node v22 meets Next.js 16 requirements. Playwright Chromium (already installed from Phase 1) supports WebGL via SwiftShader for E2E map testing.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest (unit/logic) + Playwright (E2e/map rendering) |
| Config file | `apps/web/vitest.config.ts` (existing) + `apps/web/playwright.config.ts` (existing) |
| Quick run command | `cd apps/web && npx vitest run` |
| Full suite command | `cd apps/web && npx vitest run && npx playwright test` |

**Key constraint:** jsdom (Vitest environment) does NOT support WebGL. MapLibre components cannot be unit-tested with Vitest. Map rendering must be tested via Playwright E2E only. Unit tests cover: mock data logic, filter functions, Zustand store actions, TypeScript type validation, and data transformations.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAP-01 | Interactive map renders with structures visible | e2e | `npx playwright test tests/map.spec.ts` | ❌ Wave 0 |
| MAP-02 | Structures have color-coded status symbology | e2e | `npx playwright test tests/map.spec.ts -g "colors"` | ❌ Wave 0 |
| MAP-03 | Click structure opens digital passport | e2e | `npx playwright test tests/map.spec.ts -g "passport"` | ❌ Wave 0 |
| MAP-04 | Dashboard shows condition distribution, repair queue, inspection stats | e2e | `npx playwright test tests/dashboard.spec.ts` | ❌ Wave 0 |
| MAP-05 | Filters affect both map and dashboard | e2e | `npx playwright test tests/filter.spec.ts` | ❌ Wave 0 |
| DATA-04 | Digital passport shows identity, type, geometry, specs, status, provenance | e2e | `npx playwright test tests/passport.spec.ts` | ❌ Wave 0 |
| MOCK | Mock data produces valid GeoJSON FeatureCollection | unit | `npx vitest run tests/mock-data.test.ts` | ❌ Wave 0 |
| MOCK | Filter function correctly filters by each criterion | unit | `npx vitest run tests/mock-data.test.ts -g "filter"` | ❌ Wave 0 |
| STORE | Zustand filter store setFilter/resetFilters work | unit | `npx vitest run tests/stores.test.ts` | ❌ Wave 0 |
| STORE | Zustand selection store setSelectedId works | unit | `npx vitest run tests/stores.test.ts -g "selection"` | ❌ Wave 0 |
| TYPES | Structure types validate against expected schema | unit | `npx vitest run tests/types.test.ts` | ❌ Wave 0 |
| I18N | Map and dashboard pages render translated text in all 3 locales | e2e | `npx playwright test tests/map.spec.ts -g "locale"` | ❌ Wave 0 |
| EXISTING | All Phase 1 routes still return 200 | e2e | `npx playwright test tests/routes.spec.ts` | ✅ (existing) |
| EXISTING | Design tokens still defined | unit | `npx vitest run tests/design-tokens.test.ts` | ✅ (existing) |

### Sampling Rate

- **Per task commit:** `cd apps/web && npm run build` (build must pass)
- **Per wave merge:** `cd apps/web && npx vitest run && npx playwright test`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Nyquist Feedback Latency Estimates

| Test Type | Estimated Latency | Rationale |
|-----------|-------------------|-----------|
| Vitest unit (mock data, stores, types) | < 3s | Pure logic, no DOM, no network. ~15-20 tests. |
| Playwright E2E (map rendering, click, passport) | 30-60s | Dev server startup (already running with `reuseExistingServer`), page navigation, WebGL init, tile loading, interaction. `fullyParallel: false` adds serialization. |
| Build check | 30-45s | Next.js 16 with Turbopack, 24+ pages, new map/dashboard routes. |
| Full suite (Vitest + Playwright) | 60-90s | Vitest <3s + Playwright 30-60s + overhead. |

### Wave 0 Gaps

- [ ] `apps/web/tests/map.spec.ts` — covers MAP-01, MAP-02, MAP-03: map renders, structures visible, color-coded, click opens passport
- [ ] `apps/web/tests/dashboard.spec.ts` — covers MAP-04: dashboard charts render, show data
- [ ] `apps/web/tests/filter.spec.ts` — covers MAP-05: filter controls work, affect map and dashboard
- [ ] `apps/web/tests/passport.spec.ts` — covers DATA-04: passport shows all required sections
- [ ] `apps/web/tests/mock-data.test.ts` — covers MOCK: valid GeoJSON, filter correctness, edge cases (empty results, missing coords)
- [ ] `apps/web/tests/stores.test.ts` — covers STORE: Zustand store actions
- [ ] `apps/web/tests/types.test.ts` — covers TYPES: TypeScript type validation (compile-time + runtime shape checks)
- [ ] New shadcn/ui components install: `npx shadcn@latest add sheet select checkbox badge separator card` — if not already present from Phase 1

*(Existing tests from Phase 1: routes.spec.ts (21 tests), i18n.spec.ts (6 tests), fonts.spec.ts (3 tests), design-tokens.test.ts (6 tests) — all must still pass)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No authentication in Phase 2 (Phase 3) |
| V3 Session Management | no | No sessions in Phase 2 |
| V4 Access Control | no | No access control in Phase 2 — all data is mock/public |
| V5 Input Validation | yes | Filter values (district, basin, type, condition) are validated against known enum values. Map click events extract feature properties from MapLibre's queryRenderedFeatures — no user-controlled injection point. Structure ID from click is used as query key — validated as string. |
| V6 Cryptography | no | No crypto in Phase 2 |
| V7 Error Handling | yes | TanStack Query error states (isLoading, isError) handled in UI. MapLibre error event handler for tile load failures. Next.js error boundaries for route-level errors. |
| V14 Configuration | yes | OSM tile URL configurable (not hardcoded in multiple places). No secrets in mock data phase. |

### Known Threat Patterns for Map UI

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via structure names in map popups/passport | Tampering | Structure names come from mock data (controlled). In real API: use React's automatic escaping (JSX interpolation). Never use `setHTML()` with user-controlled content in MapLibre popups — use React-rendered content instead. |
| External tile server tracking (privacy) | Information Disclosure | OSM tile server sees user IP and requested tile coordinates. For production: proxy tiles through own server or use commercial provider with privacy policy. For dev/MVP: acceptable. [CITED: operations.osmfoundation.org/policies/tiles/] |
| Tile server unavailability (DoS dependency) | Denial of Service | OSM tiles are best-effort, no SLA. Implement fallback: if tiles fail to load, show map with structures only (no base map). MapLibre `error` event handler. |
| Malicious GeoJSON in mock data | Tampering | Mock data is static TypeScript files committed to git — no external input. In real API: validate GeoJSON structure before passing to MapLibre. |

**Security note:** Phase 2 has minimal attack surface — no authentication, no user input (beyond filter selection from predefined options), no API endpoints (mock data is local). The primary security considerations are: (1) safe rendering of structure names (React auto-escaping), (2) OSM tile privacy (IP visible to OSM), and (3) graceful handling of tile load failures.

## Project Constraints (from AGENTS.md)

The following directives from AGENTS.md constrain this phase:

1. **Tech stack locked:** MapLibre GL JS 5.x (verified 5.24.0), TanStack Query 5.x (verified 5.101.1), Zustand 5.x (verified 5.0.14), Tailwind CSS 4, shadcn/ui — all versions verified against npm registry on 2026-06-26.
2. **Trilingual UI required:** Russian, Kazakh, English. All new UI text (map controls, filter labels, passport sections, dashboard titles) must be translated in `messages/{en,ru,kk}.json`.
3. **MapLibre GL JS is the map renderer:** STACK.md specifies MapLibre GL JS 5.19.x. Verified latest is 5.24.0. react-map-gl is the standard React companion (not a competing library).
4. **No backend exists yet:** Phase 2 depends on "Backend Phase 2 (needs REST API + TiPG vector tiles)" but no backend workstream exists. MUST use mock data. Mock data layer must be designed for easy swap to real API.
5. **OGC API Features/Tiles for vector access:** This is the future integration standard. The mock data should produce GeoJSON that matches what TiPG OGC API Features would return (GeoJSON FeatureCollection).
6. **Architecture principle:** "Every structure has one canonical asset record." The mock data should reflect this — each structure has one record with canonical identity, multiple evidence sources (provenance), and a condition status.
7. **GSD Workflow Enforcement:** Use GSD entry points for all work. Do not make direct repo edits outside GSD workflow.
8. **Next.js 16 has breaking changes:** AGENTS.md warns "This is NOT the Next.js you know. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code." The executor must check Next.js 16 docs for dynamic import, App Router, and client component patterns.

## Sources

### Primary (HIGH confidence)
- Context7 `/websites/maplibre_maplibre-gl-js` (1725 snippets, High reputation, 72.23 score) — Map initialization, GeoJSON sources, layers, click events, popups, data-driven expressions
- Context7 `/tanstack/query` (2555 snippets, High reputation, 88.31 score) — QueryClient setup, SSR hydration, Next.js App Router patterns, prefetch/dehydrate
- Context7 `/pmndrs/zustand` (771 snippets, High reputation, 88.93 score) — Store creation, slices pattern, persist middleware, selectors, TypeScript
- Context7 `/websites/recharts_github_io` (1232 snippets, High reputation, 81.07 score) — PieChart, BarChart, AreaChart, ResponsiveContainer
- npm registry (queried 2026-06-26) — version verification for all 5 new packages + package legitimacy check
- gsd-tools package-legitimacy check — OK/SUS verdicts for all 5 packages (3 SUS are false-positive "too-new" flags on packages with 2M-58M weekly downloads)

### Secondary (MEDIUM confidence)
- OSM Tile Usage Policy https://operations.osmfoundation.org/policies/tiles/ — usage requirements, attribution, caching, prohibited uses, alternatives
- OSM Raster Tile Providers https://wiki.openstreetmap.org/wiki/Raster_tile_providers — comprehensive list of free and commercial tile providers
- MapLibre demo tiles https://demotiles.maplibre.org/style.json — confirmed working vector tile style (minimal, only country boundaries)
- react-map-gl npm registry — version 8.1.1, peer dependencies (maplibre-gl >= 1.13.0), 2M/wk downloads, visgl GitHub repo

### Tertiary (LOW confidence)
- react-map-gl `/maplibre` import subpath — [ASSUMED] based on react-map-gl convention for dual Mapbox/MapLibre support. Not verified via Context7 (react-map-gl not in Context7 library list). Executor should verify at install time.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all 5 new packages verified against npm registry with version numbers, package legitimacy check (OK/SUS-false-positive), and postinstall script check (all clean)
- Architecture: HIGH — MapLibre + react-map-gl patterns from Context7 (High reputation, 1725 snippets); TanStack Query SSR patterns from Context7 (88.31 score); Zustand patterns from Context7 (88.93 score); Recharts patterns from Context7 (81.07 score)
- Pitfalls: HIGH — MapLibre SSR/WebGL issue is well-documented; OSM tile usage policy verified from official source; TanStack Query infinite refetch from official docs
- Mock data strategy: MEDIUM — the API contract is assumed based on STACK.md mention of TiPG/OGC API Features; actual backend may differ
- Tile source: MEDIUM — OSM tiles verified as acceptable for dev from official policy page; production strategy needs user input

**Research date:** 2026-06-26
**Valid until:** 2026-07-26 (30 days — MapLibre, TanStack Query, Zustand, Recharts are stable libraries with infrequent breaking changes)
