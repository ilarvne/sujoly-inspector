'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useLiveQuery } from 'dexie-react-hooks';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { db } from '@/lib/db/field-db';
import { applyResolution, hasUnresolvedConflicts } from '@/lib/sync/conflict-resolution';
import type { ConflictField, FieldInspection } from '@/lib/db/types';

export function ConflictResolutionDialog({
  inspectionId,
  onClose,
}: {
  inspectionId: number;
  onClose: () => void;
}) {
  const t = useTranslations('sync');
  const [conflicts, setConflicts] = useState<ConflictField[]>([]);

  const inspection = useLiveQuery(() => db.fieldInspections.get(inspectionId));

  useEffect(() => {
    if (inspection?.conflictData) {
      setConflicts(inspection.conflictData);
    }
  }, [inspection]);

  const handleResolve = (index: number, resolution: 'local' | 'server') => {
    setConflicts((prev) =>
      prev.map((c, i) => (i === index ? { ...c, resolution } : c))
    );
  };

  const handleApply = async () => {
    if (!inspection || hasUnresolvedConflicts(conflicts)) return;

    const resolved = applyResolution(inspection, conflicts);
    await db.fieldInspections.update(inspectionId, {
      ...resolved,
      syncStatus: 'confirmed',
      conflictData: undefined,
      updatedAt: new Date().toISOString(),
    });

    await db.syncQueue
      .where('inspectionId')
      .equals(inspectionId)
      .modify({ status: 'confirmed', updatedAt: new Date().toISOString() });

    onClose();
  };

  const handleResolveAll = (resolution: 'local' | 'server') => {
    setConflicts((prev) =>
      prev.map((c) => ({ ...c, resolution }))
    );
  };

  if (!inspection) return null;

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl" data-testid="conflict-dialog">
        <DialogHeader>
          <DialogTitle>{t('conflictTitle')}</DialogTitle>
          <DialogDescription>{t('conflictDescription')}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 max-h-[400px] overflow-y-auto">
          {conflicts.map((conflict, index) => (
            <div key={index} className="space-y-2 rounded-md border p-3">
              <Label className="text-sm font-semibold">{conflict.label}</Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">{t('localValue')}</span>
                  <div className="rounded bg-muted p-2 text-sm">
                    {String(conflict.localValue ?? '—')}
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground">{t('serverValue')}</span>
                  <div className="rounded bg-muted p-2 text-sm">
                    {String(conflict.serverValue ?? '—')}
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={conflict.resolution === 'local' ? 'default' : 'outline'}
                  onClick={() => handleResolve(index, 'local')}
                  data-testid={`conflict-${index}-local`}
                >
                  {t('acceptLocal')}
                </Button>
                <Button
                  size="sm"
                  variant={conflict.resolution === 'server' ? 'default' : 'outline'}
                  onClick={() => handleResolve(index, 'server')}
                  data-testid={`conflict-${index}-server`}
                >
                  {t('acceptServer')}
                </Button>
              </div>
            </div>
          ))}
        </div>

        <Separator />

        <div className="flex justify-between">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleResolveAll('local')}
              data-testid="resolve-all-local"
            >
              {t('acceptLocal')} (All)
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleResolveAll('server')}
              data-testid="resolve-all-server"
            >
              {t('acceptServer')} (All)
            </Button>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            data-testid="conflict-cancel"
          >
            {t('field') === 'field' ? 'Cancel' : 'Cancel'}
          </Button>
          <Button
            onClick={handleApply}
            disabled={hasUnresolvedConflicts(conflicts)}
            data-testid="conflict-apply"
          >
            {t('resolveConflict')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
