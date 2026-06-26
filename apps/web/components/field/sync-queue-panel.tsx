'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useLiveQuery } from 'dexie-react-hooks';
import { FileTextIcon, ImageIcon, MicIcon, RefreshCwIcon, AlertTriangleIcon } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { db } from '@/lib/db/field-db';
import { useConnectivityStore } from '@/lib/stores/connectivity-store';
import { processSyncQueue } from '@/lib/sync/sync-engine';
import { SyncStatusBadge } from './sync-status-badge';
import { ConflictResolutionDialog } from './conflict-resolution-dialog';
import { VoiceTranscriptionStatus } from './voice-transcription-status';
import type { RecordType } from '@/lib/db/types';

const recordTypeIcons: Record<RecordType, typeof FileTextIcon> = {
  inspection: FileTextIcon,
  photo: ImageIcon,
  voice_note: MicIcon,
};

export function SyncQueuePanel() {
  const t = useTranslations('sync');
  const tField = useTranslations('field');
  const isOnline = useConnectivityStore((s) => s.isOnline);
  const [conflictInspectionId, setConflictInspectionId] = useState<number | null>(null);

  const entries = useLiveQuery(async () => {
    const queue = await db.syncQueue.toArray();
    const inspections = await db.fieldInspections.toArray();
    return queue
      .map((entry) => ({
        ...entry,
        inspection: inspections.find((i) => i.id === entry.inspectionId),
      }))
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  });

  const pendingEntries = entries?.filter((e) =>
    ['pending', 'failed', 'conflict', 'syncing'].includes(e.status)
  );

  const hasConflicts = entries?.some((e) => e.status === 'conflict');

  const handleSync = () => {
    if (isOnline) {
      processSyncQueue();
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{t('queueTitle')}</CardTitle>
          {pendingEntries && pendingEntries.length > 0 && isOnline && (
            <Button variant="outline" size="sm" onClick={handleSync} data-testid="panel-sync-btn">
              <RefreshCwIcon className="size-4 mr-2" />
              {t('syncNow')}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {!pendingEntries || pendingEntries.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('queueEmpty')}</p>
        ) : (
          <ScrollArea className="h-[400px] w-full pr-4">
            <div className="space-y-3">
              {pendingEntries.map((entry) => {
                const Icon = recordTypeIcons[entry.recordType];
                return (
                  <div
                    key={entry.id}
                    className="rounded-md border p-3 space-y-2"
                    data-testid={`queue-entry-${entry.id}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Icon className="size-4 text-muted-foreground" />
                        <div>
                          <div className="text-sm font-medium">
                            {entry.inspection?.structureId || `#${entry.inspectionId}`}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {entry.inspection?.structureName || ''}
                          </div>
                        </div>
                      </div>
                      <SyncStatusBadge status={entry.status} />
                    </div>

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{t('recordType')}: {entry.recordType}</span>
                      <span>{t('recordDate')}: {entry.createdAt.split('T')[0]}</span>
                    </div>

                    {entry.lastError && (
                      <div className="text-xs text-destructive">
                        {entry.lastError}
                      </div>
                    )}

                    {entry.status === 'conflict' && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => setConflictInspectionId(entry.inspectionId)}
                        data-testid={`resolve-conflict-${entry.inspectionId}`}
                      >
                        <AlertTriangleIcon className="size-4 mr-2" />
                        {t('resolveConflict')}
                      </Button>
                    )}

                    {entry.recordType === 'voice_note' && entry.inspection && (
                      <VoiceTranscriptionStatus inspectionId={entry.inspectionId} />
                    )}

                    {entry.status === 'confirmed' && entry.inspection && (
                      <VoiceTranscriptionStatus inspectionId={entry.inspectionId} />
                    )}
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}

        {hasConflicts && (
          <>
            <Separator className="my-3" />
            <p className="text-xs text-muted-foreground">
              {t('conflictDescription')}
            </p>
          </>
        )}

        {conflictInspectionId !== null && (
          <ConflictResolutionDialog
            inspectionId={conflictInspectionId}
            onClose={() => setConflictInspectionId(null)}
          />
        )}
      </CardContent>
    </Card>
  );
}
