# Phase 5: PWA Field Mode - Research

**Researched:** 2026-06-26
**Domain:** PWA, offline capture, deferred sync, voice transcription, IndexedDB
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FIELD-01 | Inspector can install the PWA on any device and use it offline in the field | Serwist service worker with runtime caching for pages/assets. manifest.json with installable metadata. SerwistProvider in layout for SW registration. |
| FIELD-02 | Inspector can capture photos, dictate voice notes (KK/RU), pin corrected coordinates, and fill inspection forms while offline | Dexie.js IndexedDB database for offline storage of field inspections, photos (as Blob references), voice notes (as Blob + metadata), GPS corrections. Field inspection form component with photo capture (file input + camera), voice recording (MediaRecorder API), GPS correction (geolocation API). |
| FIELD-03 | System syncs field captures when connectivity returns using deferred sync with field-level merge conflict resolution | Sync engine that processes IndexedDB sync queue when online. Field-level merge: compare each field of the local record vs server record, keep most recent per field with conflict tracking. NOT last-write-wins. |
| FIELD-04 | System transcribes voice notes to text post-sync using Kazakh and Russian speech-to-text APIs | Mock transcription service that simulates KK/RU speech-to-text API call. Transcription triggered post-sync for voice notes with status 'pending_transcription'. Shows transcription text in UI once complete. |
| FIELD-05 | Inspector can see per-record sync status (pending/syncing/confirmed/failed) and resolve conflicts via review UI | Sync status badge per record (pending/syncing/confirmed/failed/conflict). Sync queue panel showing all pending records. Conflict resolution dialog showing field-by-field comparison with accept local/accept server/merge options. |
</phase_requirements>

## Summary

Phase 5 transforms the existing Next.js app into an installable PWA with full offline field inspection capability. The core additions are:

1. **Serwist service worker**: Wraps the Next.js config to inject a service worker with runtime caching for all pages and assets. The SW caches pages on navigation and serves from cache when offline. A manifest.json makes the app installable on desktop/mobile.

2. **Dexie.js IndexedDB layer**: A local database (`sujoly-field-db`) with tables for field inspections, photos, voice notes, and a sync queue. All field captures are written to IndexedDB first, then synced when connectivity returns. The `dexie-react-hooks` package provides `useLiveQuery` for reactive queries.

3. **Sync engine with field-level merge**: A sync engine processes the IndexedDB sync queue when the browser detects online status. For each record, it compares local vs server field-by-field (not whole-record last-write-wins). Conflicts are flagged for manual resolution.

4. **Voice transcription service**: A mock service that simulates sending audio to a KK/RU speech-to-text API. In production, this would call a real API (e.g., Yandex SpeechKit, Google Cloud Speech-to-Text with kk/ru locales). The mock returns placeholder text with language indication.

5. **Field mode UI**: A `/field` route with a comprehensive inspection form supporting photo capture, voice recording, GPS correction, and structured findings. A sync status indicator in the header shows online/offline state and pending sync count. A sync queue panel lists all pending records with per-record status.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Service worker caching | Browser (SW) | — | Serwist SW intercepts fetch, caches responses, serves from cache offline |
| Offline data persistence | Browser (IndexedDB) | — | Dexie.js manages IndexedDB tables for inspections, photos, voice notes, sync queue |
| Sync queue processing | Browser | — | Sync engine runs in client, processes queue on 'online' event |
| Conflict resolution | Browser | — | Field-level merge logic runs client-side, conflicts surfaced for manual review |
| Voice transcription | Browser (mock) | Server (future) | Mock transcription in browser; real API call would be server-side proxy |
| Online/offline detection | Browser | — | Navigator.onLine + online/offline events tracked in Zustand store |
| PWA installation | Browser | — | manifest.json + SW registration enables Add to Home Screen |

## Standard Stack

### Phase 5 New Packages

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @serwist/next | latest | PWA service worker build integration for Next.js | Officially recommended by Next.js PWA docs. Wraps Next.js config, generates SW from source, injects precache manifest. [VERIFIED: Context7 /websites/serwist_pages_dev] |
| serwist | latest | Core SW library (runtime caching, precaching) | Serwist's core. Provides Serwist class, caching strategies, PrecacheEntry types. [VERIFIED: Context7] |
| dexie | 4.x | IndexedDB wrapper for offline data | Minimalistic, Promise-based API, TypeScript support, EntityTable typing. 241 snippets in Context7. [VERIFIED: Context7 /dexie/dexie.js] |
| dexie-react-hooks | 1.x | React hooks for Dexie (useLiveQuery) | Reactive queries that auto-update when IndexedDB changes. Official Dexie companion. [VERIFIED: Context7] |

### Existing (from Phases 1-3, not re-installed)

| Library | Version | Purpose |
|---------|---------|---------|
| next | 16.2.9 | App Router, SSR/SSG, PWA shell |
| react / react-dom | 19.2.4 | UI library |
| next-intl | 4.13.0 | Trilingual i18n |
| @tanstack/react-query | 5.101.1 | Server state (online data) |
| zustand | 5.0.14 | Client state (stores) |
| shadcn/ui (radix-ui) | 4.11.0 (CLI) | UI components |
| tailwindcss | 4.x | Styling |
| lucide-react | 1.21.0 | Icons |

## Architecture Patterns

### System Architecture Diagram

```
Browser (Client)
    │
    ├── Service Worker (public/sw.js)
    │   └── Serwist runtime caching (pages, assets, images, fonts)
    │   └── Offline fallback page
    │
    ├── IndexedDB (sujoly-field-db)
    │   ├── fieldInspections table (offline inspection records)
    │   ├── fieldPhotos table (photo Blob references + metadata)
    │   ├── fieldVoiceNotes table (audio Blob + metadata + transcription)
    │   └── syncQueue table (sync operations with status)
    │
    ├── /field route (new)
    │   └── FieldInspectionForm ('use client')
    │       ├── Structure select (from mock data)
    │       ├── Findings textarea
    │       ├── Condition select
    │       ├── PhotoCapture (file input / camera)
    │       ├── VoiceNoteRecorder (MediaRecorder API)
    │       ├── GPSCorrection (geolocation + manual lat/lon input)
    │       └── Save → writes to IndexedDB + sync queue
    │
    ├── Sync Engine (lib/sync/sync-engine.ts)
    │   ├── Listens to 'online' event
    │   ├── Processes syncQueue entries
    │   ├── Field-level merge conflict resolution
    │   ├── Updates record status (pending → syncing → confirmed/failed/conflict)
    │   └── Triggers voice transcription post-sync
    │
    ├── UI Components
    │   ├── FieldModeIndicator (header — online/offline + pending count)
    │   ├── SyncStatusBadge (per-record status: pending/syncing/confirmed/failed/conflict)
    │   ├── SyncQueuePanel (list of pending/failed records)
    │   ├── ConflictResolutionDialog (field-by-field comparison)
    │   └── VoiceTranscriptionStatus (transcription pending/complete)
    │
    └── State Management
        ├── useConnectivityStore (Zustand) ← isOnline, pendingSyncCount
        ├── useFieldModeStore (Zustand, persist) ← fieldMode enabled, lastSyncAt
        ├── useAuthStore (existing) ← user role for field mode access
        └── Dexie useLiveQuery ← reactive IndexedDB queries
```

### Recommended Project Structure (additions)

```
apps/web/
├── app/
│   ├── [locale]/
│   │   ├── field/
│   │   │   └── page.tsx              # Server Component: field mode page
│   │   ├── ~offline/
│   │   │   └── page.tsx              # Server Component: offline fallback
│   │   └── layout.tsx                # Modified: add SerwistProvider, manifest, SW register
│   └── sw.ts                         # Service worker source (compiled to public/sw.js)
├── public/
│   ├── manifest.json                 # PWA manifest
│   └── icons/                        # PWA icons (192, 512, maskable)
├── components/
│   ├── pwa/
│   │   └── sw-register.tsx           # 'use client' — SW registration
│   ├── field/
│   │   ├── field-inspection-form.tsx # 'use client' — main inspection form
│   │   ├── photo-capture.tsx         # 'use client' — photo capture UI
│   │   ├── voice-note-recorder.tsx   # 'use client' — voice recording UI
│   │   ├── gps-correction.tsx        # 'use client' — GPS correction UI
│   │   ├── field-mode-indicator.tsx  # 'use client' — header online/offline indicator
│   │   ├── sync-status-badge.tsx     # 'use client' — per-record status badge
│   │   ├── sync-queue-panel.tsx      # 'use client' — sync queue list
│   │   └── conflict-resolution-dialog.tsx # 'use client' — conflict resolution
│   └── layout/
│       └── app-shell.tsx             # Modified: add FieldModeIndicator to header
├── lib/
│   ├── db/
│   │   ├── field-db.ts               # Dexie database definition
│   │   └── types.ts                  # Field capture types
│   ├── stores/
│   │   ├── connectivity-store.ts     # Zustand: online/offline state
│   │   └── field-mode-store.ts       # Zustand: field mode settings
│   └── sync/
│       ├── sync-engine.ts            # Sync queue processor
│       ├── conflict-resolution.ts    # Field-level merge logic
│       └── voice-transcription.ts    # Mock KK/RU speech-to-text
├── messages/
│   ├── en.json                       # Modified: add field, sync, pwa namespaces
│   ├── ru.json
│   └── kk.json
└── tests/
    ├── field-db.test.ts              # Dexie db unit tests
    ├── sync-engine.test.ts           # Sync engine unit tests
    └── field.spec.ts                 # E2E test for field mode
```

## Common Pitfalls

### Pitfall 1: Serwist + Turbopack Build Compatibility
**What goes wrong:** `@serwist/next` config wrapper uses webpack plugins. Next.js 16 with Turbopack may not run webpack plugins.
**How to avoid:** If `@serwist/next` build fails with Turbopack, fall back to manual SW: create static `public/sw.js` using Serwist core APIs with runtime caching only (no precache manifest). Register SW manually via a client component.

### Pitfall 2: IndexedDB in SSR
**What goes wrong:** Dexie tries to access IndexedDB during server-side rendering, causing "indexedDB is not defined" error.
**How to avoid:** All Dexie operations must be in 'use client' components or in useEffect hooks. The database instance can be created at module level (Dexie defers IndexedDB access until operations are called), but queries must run client-side only.

### Pitfall 3: MediaRecorder API Availability
**What goes wrong:** MediaRecorder API is not available in all browsers (especially older ones) or requires HTTPS.
**How to avoid:** Check `typeof MediaRecorder !== 'undefined'` before using. Show a fallback message if not available. In development (HTTP), MediaRecorder may not work — handle gracefully.

### Pitfall 4: Blob Storage in IndexedDB
**What goes wrong:** Storing large Blobs (photos, audio) in IndexedDB can hit storage quotas.
**How to avoid:** Store Blobs directly in IndexedDB (it supports Blob type). For very large files, consider storing in Cache API instead. For MVP, photos are compressed/resized before storage. Set reasonable size limits (10MB per photo, 5MB per voice note).

### Pitfall 5: Service Worker in Development
**What goes wrong:** SW caches pages in development, causing stale content during iteration.
**How to avoid:** Disable SW registration in development (`process.env.NODE_ENV === 'development'`). Or use SerwistProvider's `disable` prop. The SW is only active in production builds.

### Pitfall 6: Sync Engine Race Conditions
**What goes wrong:** Multiple sync attempts run simultaneously when connectivity flickers.
**How to avoid:** Use a mutex/flag in the sync engine to prevent concurrent sync runs. Track `isSyncing` state and skip if already syncing.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | @serwist/next config wrapper works with Next.js 16.2.9 Turbopack builds | PWA | If not, fall back to manual SW with runtime caching only. |
| A2 | Dexie.js 4.x works with React 19 and Next.js 16 | Data | Dexie is framework-agnostic. dexie-react-hooks should work with React 19. |
| A3 | MediaRecorder API is available in target browsers (Chrome, Edge) | Voice | Field inspectors likely use Chrome on Android. MediaRecorder is well-supported in modern Chrome. |
| A4 | IndexedDB storage quota is sufficient for field inspection data | Storage | Typical inspection: 3-5 photos (1-5MB each) + 1-2 voice notes (1-3MB each). ~20MB per inspection. IndexedDB quota is usually 50% of disk space. |
| A5 | Navigator.onLine and online/offline events reliably detect connectivity | Sync | These can be unreliable (false positives). For MVP, trust these events. Production would use heartbeat/ping. |

## Open Questions

1. **Should voice transcription be real or mock?**
   - Recommendation: **Mock for MVP**. Real KK/RU speech-to-text requires API keys and server-side proxy. Mock returns placeholder transcription text. The interface is designed for easy swap to real API.

2. **Should GPS correction use device GPS or manual entry?**
   - Recommendation: **Both**. Auto-fetch via Geolocation API with a manual override input for lat/lon. Inspector can correct coordinates by typing or by using device GPS.

3. **Should the sync engine use Background Sync API?**
   - Recommendation: **No for MVP**. Background Sync API requires SW integration and has limited browser support. Use foreground sync triggered by 'online' event. Sufficient for field inspector workflow (they open the app to sync).
