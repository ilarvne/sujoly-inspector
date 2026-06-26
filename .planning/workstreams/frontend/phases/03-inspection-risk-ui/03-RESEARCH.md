# Phase 3: Inspection & Risk UI - Research

**Researched:** 2026-06-26
**Domain:** Inspection timeline, document upload, risk score display, RBAC, engineer overrides, export UI
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-05-FE | User can view inspection history timeline per structure (date, inspector, findings, photos, condition at time of inspection) | Vertical timeline component with date entries, inspector name, findings text, photo thumbnails, condition badge. Data from mock inspection records via TanStack Query. Integrated as a tab in the passport panel. |
| DATA-06-FE | User can attach documents (scanned passports, inspection reports, photos) to structure records via upload UI | File upload component with drag-and-drop or file input, mock presigned URL flow, document list with download links. Integrated as a tab in the passport panel. |
| RISK-06-FE | User with engineer role can override system-recommended inspection intervals and repair statuses via UI with logged provenance | Engineer override dialog with field selection (inspection interval, repair status), original vs new value, reason textarea, and provenance log display. Gated by auth role. |
| RISK-07-FE | UI enforces role-appropriate access (administrator, engineer, inspector, viewer) with login and permission gating | Mock auth Zustand store with 4 roles (admin, engineer, inspector, viewer), login page, permission guard component, role-based UI visibility. |
| RISK-08-FE | User can export structure lists as CSV/GeoJSON and generate inspection reports as PDF from the UI in all three languages | PapaParse for CSV generation, native GeoJSON serialization, jsPDF + jspdf-autotable for PDF inspection reports. Export panel on /reports page with format selection. |
</phase_requirements>

## Summary

Phase 3 extends the Phase 2 map/passport foundation with inspection history, document management, risk visualization, role-based access control, and data export. The backend does not exist yet — all data is mock. The mock data layer extends the existing `lib/api/mock-data.ts` and `lib/api/client.ts` with new types and query hooks for inspections, documents, risk scores, and engineer overrides.

The core architectural decisions:

1. **Passport panel becomes tabbed**: The existing `PassportPanel` Sheet from Phase 2 is refactored to use shadcn/ui Tabs with 4 tabs: Overview (existing Phase 2 content), Inspections (timeline), Risk (score + override), Documents (upload + list). This keeps all structure-level information in one unified panel accessible from the map.

2. **Mock RBAC via Zustand**: A `useAuthStore` Zustand store manages mock authentication state (current user, role). Four roles: admin, engineer, inspector, viewer. Login page at `/[locale]/login` with role selection. The store persists to localStorage for session continuity. No real authentication — this is a frontend mock that will be swapped for real JWT/OAuth when the backend is ready.

3. **Client-side export**: CSV via PapaParse (5.5.4), GeoJSON via native `JSON.stringify`, PDF via jsPDF (4.2.1) + jspdf-autotable (5.0.8). All exports are generated client-side from mock data. PDF inspection reports use jsPDF text/table APIs for structured layout.

4. **Form validation**: react-hook-form (7.80.0) + zod (4.4.3) + @hookform/resolvers (5.4.0) for the engineer override form and login form. shadcn/ui Form component wraps react-hook-form.

5. **Date handling**: date-fns (4.4.0) for date formatting in the inspection timeline and export reports.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Inspection timeline rendering | Browser | — | Client component reads from TanStack Query cache, renders vertical timeline with dates, findings, photos |
| Document upload UI | Browser | — | File input with drag-and-drop, mock presigned URL generation, upload progress simulation |
| Risk score visualization | Browser | — | Client component renders score gauge (Progress), component breakdown (Bars/Progress), explanation text |
| Engineer override form | Browser | — | react-hook-form + zod validation, dialog with field selection, reason input, provenance log |
| RBAC / auth state | Browser | — | Zustand store persisted to localStorage, permission guard component wraps protected UI |
| Export generation | Browser | — | PapaParse for CSV, JSON.stringify for GeoJSON, jsPDF for PDF — all client-side, triggered by download |
| i18n for new sections | Frontend Server (SSR) | Browser | next-intl getTranslations in server pages, useTranslations in client subcomponents |

## Standard Stack

### Core (Phase 3 new packages)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-hook-form | 7.80.0 | Form management for engineer override and login forms | Industry standard React form library. Performant, flexible, 7M+/wk downloads. [VERIFIED: npm registry] |
| zod | 4.4.3 | Schema validation for form inputs | TypeScript-first validation. Pairs with react-hook-form via @hookform/resolvers. 40M+/wk downloads. [VERIFIED: npm registry] |
| @hookform/resolvers | 5.4.0 | Adapter connecting zod schemas to react-hook-form | Official resolver package from react-hook-form team. [VERIFIED: npm registry] |
| papaparse | 5.5.4 | CSV generation from structure data | Battle-tested CSV parser/generator. Handles edge cases (commas, quotes, newlines in fields). 14M+/wk downloads. [VERIFIED: npm registry] |
| jspdf | 4.2.1 | Client-side PDF generation for inspection reports | Standard client-side PDF library. Text, tables, page layout. [VERIFIED: npm registry] |
| jspdf-autotable | 5.0.8 | PDF table generation plugin for jsPDF | Adds table support to jsPDF for structured inspection reports. [VERIFIED: npm registry] |
| date-fns | 4.4.0 | Date formatting for timeline and reports | Modern date utility, tree-shakeable, locale support. 16M+/wk downloads. [VERIFIED: npm registry] |

### Existing (from Phases 1-2, not re-installed)

| Library | Version | Purpose |
|---------|---------|---------|
| next | 16.2.9 | App Router, SSR/SSG |
| react / react-dom | 19.2.4 | UI library |
| next-intl | 4.13.0 | Trilingual i18n |
| @tanstack/react-query | 5.101.1 | Data fetching/caching |
| zustand | 5.0.14 | Client state management |
| shadcn/ui (radix-ui) | 4.11.0 (CLI) | UI components |
| tailwindcss | 4.x | Styling |
| lucide-react | 1.21.0 | Icons |

### shadcn/ui Components Added in Phase 3

| Component | Purpose |
|-----------|---------|
| dialog | Engineer override dialog, login dialog |
| tabs | Passport panel tab navigation (Overview, Inspections, Risk, Documents) |
| table | Inspection history table, document list table, export preview |
| tooltip | Risk component explanation tooltips |
| alert | Permission denied messages, upload error alerts |
| textarea | Engineer override reason input, inspection findings |
| label | Form field labels |
| input | Form text inputs (login, override) |
| progress | Risk score gauge, upload progress bar |
| accordion | Risk component breakdown collapsible sections |
| dropdown-menu | Export format selection, user menu |
| avatar | User profile avatar in header |
| scroll-area | Scrollable timeline and document list |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| jsPDF | browser print-to-PDF | Less control over layout, no programmatic generation. jsPDF gives structured reports. — **Use jsPDF** |
| jsPDF | pdf-lib | pdf-lib is more modern but less documented for table generation. jspdf-autotable is purpose-built. — **Use jsPDF** |
| PapaParse | Manual CSV string building | Manual CSV is error-prone with edge cases. PapaParse handles quoting/escaping. — **Use PapaParse** |
| react-hook-form | Native form handling | RHF provides validation, error handling, and integrates with zod. — **Use react-hook-form** |
| Zustand auth store | NextAuth.js | NextAuth requires backend/OAuth provider. Mock auth via Zustand is sufficient for MVP. — **Use Zustand** |
| date-fns | Intl.DateTimeFormat | Intl is built-in but lacks parsing and manipulation. date-fns provides consistent API. — **Use date-fns** |

**Installation:**
```bash
cd apps/web
npm install react-hook-form@7.80.0 zod@4.4.3 @hookform/resolvers@5.4.0 papaparse@5.5.4 jspdf@4.2.1 jspdf-autotable@5.0.8 date-fns@4.4.0
npm install -D @types/papaparse@5.5.2
```

**Version verification (executed 2026-06-26):**
```
react-hook-form:      7.80.0   (npm view)
zod:                  4.4.3    (npm view)
@hookform/resolvers:  5.4.0    (npm view)
papaparse:            5.5.4    (npm view)
jspdf:                4.2.1    (npm view)
jspdf-autotable:      5.0.8    (npm view)
date-fns:             4.4.0    (npm view)
@types/papaparse:     5.5.2    (npm view)
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| react-hook-form | npm | ~8 yrs (v7.80.0) | 7M/wk | github.com/react-hook-form/react-hook-form | OK | Approved |
| zod | npm | ~5 yrs (v4.4.3) | 40M/wk | github.com/colinhacks/zod | OK | Approved |
| @hookform/resolvers | npm | ~5 yrs (v5.4.0) | 5M/wk | github.com/react-hook-form/resolvers | OK | Approved |
| papaparse | npm | ~10 yrs (v5.5.4) | 14M/wk | github.com/mholt/PapaParse | OK | Approved |
| jspdf | npm | ~10 yrs (v4.2.1) | 6M/wk | github.com/parallax/jsPDF | OK | Approved |
| jspdf-autotable | npm | ~8 yrs (v5.0.8) | 2M/wk | github.com/simonbengtsson/jspdf-autotable | OK | Approved |
| date-fns | npm | ~10 yrs (v4.4.0) | 16M/wk | github.com/date-fns/date-fns | OK | Approved |
| @types/papaparse | npm | — | 4M/wk | DefinitelyTyped | OK | Approved |

**Postinstall script check:** All packages returned empty for postinstall scripts — no suspicious scripts detected.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Browser (Client)
    │
    ├── /map route (existing from Phase 2)
    │   └── PassportPanel ('use client', refactored with Tabs)
    │       ├── Tab: Overview (existing Phase 2 content)
    │       ├── Tab: Inspections
    │       │   └── InspectionTimeline (vertical timeline with date, inspector, findings, photos, condition)
    │       │       └── Data from useInspections(structureId) → mockInspections
    │       ├── Tab: Risk
    │       │   └── RiskScoreDisplay (score gauge, component breakdown, explanation)
    │       │       └── Data from useRiskScore(structureId) → mockRiskScore
    │       │       └── EngineerOverrideButton (gated by auth role)
    │       │           └── EngineerOverrideDialog (react-hook-form + zod)
    │       └── Tab: Documents
    │           └── DocumentUpload (file input, mock presigned URL)
    │           └── DocumentList (download links, file metadata)
    │               └── Data from useDocuments(structureId) → mockDocuments
    │
    ├── /login route (new)
    │   └── LoginForm ('use client')
    │       └── useAuthStore.login(role) → sets current user + role
    │
    ├── /reports route (replaced placeholder)
    │   └── ExportPanel ('use client')
    │       ├── CSV Export → PapaParse.unparse(structures)
    │       ├── GeoJSON Export → JSON.stringify(structureCollection)
    │       └── PDF Export → jsPDF + jspdf-autotable (inspection report)
    │
    └── State Management
        ├── useAuthStore (Zustand, new) ← user: {id, name, role} | null
        ├── useFilterStore (existing) ← filters
        ├── useSelectionStore (existing) ← selectedId
        └── useMapStore (existing) ← viewport
```

### Recommended Project Structure (additions)

```
apps/web/
├── app/
│   ├── [locale]/
│   │   ├── login/
│   │   │   └── page.tsx              # Server Component: login page
│   │   ├── reports/
│   │   │   └── page.tsx              # Server Component: replaced with ExportPanel
│   │   └── layout.tsx                # Modified: add AuthProvider
│   └── ...
├── components/
│   ├── inspection/
│   │   ├── inspection-timeline.tsx   # 'use client' — vertical timeline
│   │   └── risk-score-display.tsx    # 'use client' — score gauge + breakdown
│   ├── documents/
│   │   ├── document-upload.tsx       # 'use client' — file upload UI
│   │   └── document-list.tsx         # 'use client' — document list with download
│   ├── auth/
│   │   ├── login-form.tsx            # 'use client' — mock login form
│   │   ├── permission-guard.tsx      # 'use client' — role gating wrapper
│   │   └── user-menu.tsx             # 'use client' — header user info + logout
│   ├── override/
│   │   └── engineer-override-dialog.tsx  # 'use client' — override form dialog
│   ├── export/
│   │   ├── export-panel.tsx          # 'use client' — export format selection
│   │   └── export-utils.ts           # CSV/GeoJSON/PDF generation functions
│   ├── map/
│   │   └── passport-panel.tsx        # Modified: refactored with Tabs
│   ├── layout/
│   │   └── app-shell.tsx             # Modified: add UserMenu to header
│   └── ui/                           # New shadcn components (dialog, tabs, table, etc.)
├── lib/
│   ├── api/
│   │   ├── types.ts                  # Modified: add inspection/document/risk/override types
│   │   ├── mock-data.ts              # Modified: add mock inspections/documents/risk/overrides
│   │   └── client.ts                 # Modified: add useInspections, useDocuments, useRiskScore, useOverrides
│   └── stores/
│       └── auth-store.ts             # New: Zustand mock auth store
├── messages/
│   ├── en.json                       # Modified: add inspection, documents, risk, auth, export, override namespaces
│   ├── ru.json
│   └── kk.json
└── ...
```

### Pattern 1: Passport Panel with Tabs

**What:** The existing PassportPanel Sheet is refactored to use shadcn/ui Tabs. Four tabs: Overview (existing), Inspections (new), Risk (new), Documents (new). Each tab renders its own component.

```tsx
// components/map/passport-panel.tsx (refactored)
'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { InspectionTimeline } from '@/components/inspection/inspection-timeline';
import { RiskScoreDisplay } from '@/components/inspection/risk-score-display';
import { DocumentUpload } from '@/components/documents/document-upload';
import { DocumentList } from '@/components/documents/document-list';

// ... existing Sheet structure ...
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">{t('tabs.overview')}</TabsTrigger>
    <TabsTrigger value="inspections">{t('tabs.inspections')}</TabsTrigger>
    <TabsTrigger value="risk">{t('tabs.risk')}</TabsTrigger>
    <TabsTrigger value="documents">{t('tabs.documents')}</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">{/* existing Phase 2 content */}</TabsContent>
  <TabsContent value="inspections"><InspectionTimeline structureId={structure.id} /></TabsContent>
  <TabsContent value="risk"><RiskScoreDisplay structureId={structure.id} /></TabsContent>
  <TabsContent value="documents">
    <DocumentUpload structureId={structure.id} />
    <DocumentList structureId={structure.id} />
  </TabsContent>
</Tabs>
```

### Pattern 2: Mock Auth via Zustand with localStorage Persistence

**What:** A Zustand store manages mock authentication. Four roles with different permissions. The store persists to localStorage so the user stays "logged in" across page refreshes.

```tsx
// lib/stores/auth-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type UserRole = 'admin' | 'engineer' | 'inspector' | 'viewer';

interface AuthUser {
  id: string;
  name: string;
  role: UserRole;
}

interface AuthState {
  user: AuthUser | null;
  login: (role: UserRole) => void;
  logout: () => void;
  hasRole: (...roles: UserRole[]) => boolean;
}

const mockUsers: Record<UserRole, AuthUser> = {
  admin: { id: 'u-admin', name: 'Administrator', role: 'admin' },
  engineer: { id: 'u-engineer', name: 'Engineer', role: 'engineer' },
  inspector: { id: 'u-inspector', name: 'Inspector', role: 'inspector' },
  viewer: { id: 'u-viewer', name: 'Viewer', role: 'viewer' },
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      login: (role) => set({ user: mockUsers[role] }),
      logout: () => set({ user: null }),
      hasRole: (...roles) => {
        const user = get().user;
        return user !== null && roles.includes(user.role);
      },
    }),
    { name: 'sujoly-auth' }
  )
);
```

### Pattern 3: Permission Guard Component

**What:** A wrapper component that conditionally renders children based on the current user's role. Used to gate engineer-only UI like the override button.

```tsx
// components/auth/permission-guard.tsx
'use client';

import { useAuthStore } from '@/lib/stores/auth-store';
import type { UserRole } from '@/lib/stores/auth-store';

export function PermissionGuard({ roles, children, fallback = null }: {
  roles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const hasRole = useAuthStore((s) => s.hasRole);
  return <>{hasRole(...roles) ? children : fallback}</>;
}
```

### Pattern 4: Engineer Override Form with react-hook-form + zod

**What:** A dialog with a form for engineers to override inspection intervals or repair statuses. Uses react-hook-form with zod validation. The form records the original value, new value, reason, and engineer name for provenance.

```tsx
// components/override/engineer-override-dialog.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const overrideSchema = z.object({
  field: z.enum(['inspection_interval', 'repair_status']),
  newValue: z.string().min(1, 'Value is required'),
  reason: z.string().min(10, 'Reason must be at least 10 characters'),
});

type OverrideForm = z.infer<typeof overrideSchema>;

// Dialog with form fields: field select, new value input, reason textarea
// On submit: creates EngineerOverride record with provenance (engineer name, timestamp, original value)
```

### Pattern 5: Client-Side Export

**What:** Export functions generate files client-side from mock data. CSV via PapaParse, GeoJSON via JSON.stringify, PDF via jsPDF.

```typescript
// lib/export/export-utils.ts
import Papa from 'papaparse';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

export function exportCSV(structures: StructureFeature[]): void {
  const data = structures.map(f => ({
    id: f.properties.id,
    name: f.properties.name.ru,
    type: f.properties.type,
    condition: f.properties.condition,
    district: f.properties.district,
    basin: f.properties.basin,
  }));
  const csv = Papa.unparse(data);
  downloadBlob(csv, 'structures.csv', 'text/csv');
}

export function exportGeoJSON(collection: StructureCollection): void {
  const json = JSON.stringify(collection, null, 2);
  downloadBlob(json, 'structures.geojson', 'application/geo+json');
}

export function exportPDF(structure: StructureDetail, inspections: InspectionRecord[]): void {
  const doc = new jsPDF();
  doc.text(`Inspection Report: ${structure.name.ru}`, 14, 20);
  autoTable(doc, {
    head: [['Date', 'Inspector', 'Condition', 'Findings']],
    body: inspections.map(i => [i.date, i.inspector, i.condition, i.findings]),
    startY: 30,
  });
  doc.save(`inspection-report-${structure.id}.pdf`);
}
```

## Anti-Patterns to Avoid

- **Importing jsPDF in a Server Component:** jsPDF requires browser APIs (Blob, URL.createObjectURL). Must be in a 'use client' component or dynamically imported. [CITED: jsPDF documentation]
- **Not persisting auth state:** Without localStorage persistence, the user loses their role on page refresh. Use Zustand persist middleware. [CITED: Zustand docs]
- **Validating only on submit:** Use zod schema with react-hook-form for real-time validation feedback. [CITED: Context7 /react-hook-form/resolvers]
- **Generating PDF without table plugin:** Raw jsPDF text positioning is tedious for tabular data. Use jspdf-autotable for structured reports. [CITED: jspdf-autotable docs]
- **Storing file contents in state:** For document upload, store only metadata (filename, size, type) in state. The actual file goes to MinIO via presigned URL (mocked for now). [ASSUMED — backend will handle presigned URLs]

## Common Pitfalls

### Pitfall 1: jsPDF SSR Crash
**What goes wrong:** Build fails with "window is not defined" when jsPDF is imported in a Server Component.
**How to avoid:** Always add 'use client' to files importing jsPDF. Use dynamic import with ssr:false if needed.

### Pitfall 2: Zustand persist hydration mismatch
**What goes wrong:** Server renders with no user (null auth), client hydrates with persisted user → React hydration mismatch warning.
**How to avoid:** Use `useAuthStore` only in 'use client' components. The login page and user menu are client components. The auth state is read client-side only, not during SSR.

### Pitfall 3: File upload security
**What goes wrong:** User uploads malicious file types.
**How to avoid:** Validate file type (accept attribute on input), check file size limits, show file metadata before "upload". Mock phase doesn't actually upload — just simulates.

### Pitfall 4: CSV encoding for Cyrillic
**What goes wrong:** CSV exports with Cyrillic text show garbled characters in Excel.
**How to avoid:** Add BOM (Byte Order Mark) prefix to CSV output: `\uFEFF` + csv string. PapaParse handles this with `BOM: true` option.

### Pitfall 5: PDF Cyrillic font support
**What goes wrong:** PDF generated with jsPDF shows question marks or blank boxes instead of Cyrillic text.
**How to avoid:** jsPDF's default Helvetica font does not support Cyrillic. Either (a) embed a Unicode TTF font (e.g., Roboto) via `doc.addFont()`, or (b) transliterate Cyrillic to Latin for the PDF. For MVP, use transliteration or embed a font. The simplest approach is to use the `doc.html()` method with html2canvas which renders the browser's font rendering (including Cyrillic) as an image.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | jsPDF v4.x API is backward-compatible with v2.x for basic text/table operations | Export | If API changed significantly, export code needs adjustment. [ASSUMED — jsPDF maintains backward compatibility for core APIs] |
| A2 | Zustand persist middleware works with localStorage in Next.js client components | Auth | If persist doesn't hydrate correctly, users lose role on refresh. [ASSUMED — standard Zustand pattern] |
| A3 | shadcn/ui radix-nova style supports all 13 new components (dialog, tabs, table, etc.) | shadcn | If not, components need manual creation. [ASSUMED — radix-nova is a variant of new-york which supports all components] |
| A4 | jspdf-autotable v5.x is compatible with jsPDF v4.x | Export | If not, table export breaks. [ASSUMED — jspdf-autotable tracks jsPDF versions] |
| A5 | PapaParse unparse with BOM option produces Excel-compatible UTF-8 CSV | Export | If not, Cyrillic text garbles in Excel. [ASSUMED — PapaParse documentation mentions BOM support] |
| A6 | date-fns v4.x locale imports work with tree-shaking in Next.js | Timeline | If locale imports changed, date formatting may need adjustment. [ASSUMED — date-fns maintains locale API] |

## Open Questions

1. **Should the login be a separate page (/login) or a dialog?**
   - Recommendation: **Separate page** at `/[locale]/login`. A full page gives space for the login form and role selection. The page is accessible from the header user menu. After login, redirect to the previous page or /map.

2. **Should the engineer override be in the passport panel or a separate page?**
   - Recommendation: **Dialog from the passport panel**. The override is contextual to a specific structure. A dialog triggered from the Risk tab keeps the user in context. The dialog uses react-hook-form for structured input.

3. **Should PDF export embed a Cyrillic font or use html2canvas?**
   - Recommendation: **Use jsPDF text API with transliteration for MVP**. Embedding TTF fonts adds complexity and bundle size. Transliteration (Cyrillic → Latin) via a simple mapping is sufficient for the MVP PDF reports. The PDF is a structured data report, not a formatted document.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next.js 16 runtime | Yes | v22.21.0 | — |
| npm | Package management | Yes | 11.7.0 | — |
| Browser Blob API | Export (CSV/GeoJSON/PDF download) | Yes | — | — |
| localStorage | Auth store persistence | Yes | — | Session storage fallback |
| Internet access | npm registry | Yes | — | — |

All required tools are available.
