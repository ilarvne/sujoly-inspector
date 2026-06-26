import { db } from '@/lib/db/field-db';
import { useConnectivityStore } from '@/lib/stores/connectivity-store';
import { useFieldModeStore } from '@/lib/stores/field-mode-store';
import { detectConflicts } from './conflict-resolution';
import { transcribeVoiceNote } from './voice-transcription';
import type { SyncQueueEntry, FieldInspection } from '@/lib/db/types';

let isSyncing = false;
let syncEngineInitialized = false;

export async function processSyncQueue(): Promise<void> {
  if (isSyncing) return;
  if (typeof navigator !== 'undefined' && !navigator.onLine) return;

  isSyncing = true;

  try {
    const pendingEntries = await db.syncQueue
      .where('status')
      .anyOf(['pending', 'failed', 'conflict'])
      .toArray();

    for (const entry of pendingEntries) {
      await syncEntry(entry);
    }

    await processPendingTranscriptions();

    const remainingPending = await db.syncQueue
      .where('status')
      .anyOf(['pending', 'failed', 'conflict'])
      .count();

    useConnectivityStore.getState().setPendingSyncCount(remainingPending);
    useFieldModeStore.getState().setLastSyncAt(new Date().toISOString());
  } finally {
    isSyncing = false;
  }
}

async function syncEntry(entry: SyncQueueEntry): Promise<void> {
  await db.syncQueue.update(entry.id!, {
    status: 'syncing',
    updatedAt: new Date().toISOString(),
  });

  try {
    await new Promise((resolve) => setTimeout(resolve, 200));

    if (entry.recordType === 'inspection') {
      const inspection = await db.fieldInspections.get(entry.inspectionId);
      if (inspection) {
        const serverData: Partial<FieldInspection> = {};
        const conflicts = detectConflicts(inspection, serverData);

        if (conflicts.length > 0) {
          await db.syncQueue.update(entry.id!, {
            status: 'conflict',
            conflictData: conflicts,
            updatedAt: new Date().toISOString(),
          });
          await db.fieldInspections.update(entry.inspectionId!, {
            syncStatus: 'conflict',
            conflictData: conflicts,
          });
          return;
        }
      }
    }

    await db.syncQueue.update(entry.id!, {
      status: 'confirmed',
      updatedAt: new Date().toISOString(),
    });

    if (entry.recordType === 'inspection') {
      await db.fieldInspections.update(entry.inspectionId!, {
        syncStatus: 'confirmed',
        updatedAt: new Date().toISOString(),
      });
    }
  } catch (error) {
    await db.syncQueue.update(entry.id!, {
      status: 'failed',
      lastError: error instanceof Error ? error.message : 'Unknown error',
      attempts: entry.attempts + 1,
      updatedAt: new Date().toISOString(),
    });

    if (entry.recordType === 'inspection') {
      await db.fieldInspections.update(entry.inspectionId!, {
        syncStatus: 'failed',
      });
    }
  }
}

async function processPendingTranscriptions(): Promise<void> {
  const voiceNotes = await db.fieldVoiceNotes
    .where('transcriptionStatus')
    .equals('pending')
    .toArray();

  for (const note of voiceNotes) {
    try {
      const transcription = await transcribeVoiceNote(note.blob, note.language);
      await db.fieldVoiceNotes.update(note.id!, {
        transcriptionStatus: 'complete',
        transcriptionText: transcription,
        transcribedAt: new Date().toISOString(),
      });
    } catch (error) {
      await db.fieldVoiceNotes.update(note.id!, {
        transcriptionStatus: 'failed',
        transcriptionError: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }
}

export function initSyncEngine(): void {
  if (typeof window === 'undefined') return;
  if (syncEngineInitialized) return;
  syncEngineInitialized = true;

  window.addEventListener('online', () => {
    useConnectivityStore.getState().setOnline(true);
    processSyncQueue();
  });

  window.addEventListener('offline', () => {
    useConnectivityStore.getState().setOnline(false);
  });

  db.syncQueue
    .where('status')
    .anyOf(['pending', 'failed', 'conflict'])
    .count()
    .then((count) => useConnectivityStore.getState().setPendingSyncCount(count));

  if (navigator.onLine) {
    processSyncQueue();
  }
}
