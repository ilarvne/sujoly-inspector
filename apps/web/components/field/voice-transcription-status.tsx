'use client';

import { useTranslations } from 'next-intl';
import { useLiveQuery } from 'dexie-react-hooks';
import { Badge } from '@/components/ui/badge';
import { Loader2Icon, CheckCircle2Icon, XCircleIcon, FileTextIcon } from 'lucide-react';
import { db } from '@/lib/db/field-db';
import type { TranscriptionStatus } from '@/lib/db/types';

const statusConfig: Record<TranscriptionStatus, { icon: typeof Loader2Icon; color: string }> = {
  none: { icon: FileTextIcon, color: 'text-muted-foreground' },
  pending: { icon: Loader2Icon, color: 'text-blue-500' },
  complete: { icon: CheckCircle2Icon, color: 'text-green-500' },
  failed: { icon: XCircleIcon, color: 'text-red-500' },
};

export function VoiceTranscriptionStatus({ inspectionId }: { inspectionId: number }) {
  const t = useTranslations('sync');
  const tCommon = useTranslations('common');

  const voiceNotes = useLiveQuery(() =>
    db.fieldVoiceNotes.where('inspectionId').equals(inspectionId).toArray()
  );

  if (!voiceNotes || voiceNotes.length === 0) return null;

  return (
    <div className="space-y-1.5 rounded-md bg-muted/50 p-2" data-testid={`voice-status-${inspectionId}`}>
      {voiceNotes.map((note, index) => {
        const config = statusConfig[note.transcriptionStatus];
        const Icon = config.icon;
        const labelKey =
          note.transcriptionStatus === 'pending'
            ? 'transcriptionPending'
            : note.transcriptionStatus === 'complete'
            ? 'transcriptionComplete'
            : note.transcriptionStatus === 'failed'
            ? 'transcriptionFailed'
            : 'transcriptionPending';

        return (
          <div key={note.id || index} className="space-y-1">
            <div className="flex items-center gap-2 text-xs">
              <Icon className={`size-3.5 ${config.color} ${note.transcriptionStatus === 'pending' ? 'animate-spin' : ''}`} />
              <span className="text-muted-foreground">
                {tCommon(`locale.${note.language}`)} · {note.durationSeconds}s
              </span>
              <Badge variant="secondary" className="text-xs">
                {t(labelKey)}
              </Badge>
            </div>
            {note.transcriptionText && (
              <p className="text-xs text-foreground pl-5 border-l-2 border-muted">
                {note.transcriptionText}
              </p>
            )}
            {note.transcriptionError && (
              <p className="text-xs text-destructive pl-5">
                {note.transcriptionError}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
