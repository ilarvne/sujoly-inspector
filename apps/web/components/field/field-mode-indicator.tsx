'use client';

import { useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { WifiIcon, WifiOffIcon, RefreshCwIcon, RadioIcon } from 'lucide-react';
import { useConnectivityStore } from '@/lib/stores/connectivity-store';
import { useFieldModeStore } from '@/lib/stores/field-mode-store';
import { initSyncEngine, processSyncQueue } from '@/lib/sync/sync-engine';

export function FieldModeIndicator() {
  const t = useTranslations('sync');
  const tField = useTranslations('field');
  const isOnline = useConnectivityStore((s) => s.isOnline);
  const pendingCount = useConnectivityStore((s) => s.pendingSyncCount);
  const fieldModeEnabled = useFieldModeStore((s) => s.fieldModeEnabled);
  const enableFieldMode = useFieldModeStore((s) => s.enableFieldMode);
  const disableFieldMode = useFieldModeStore((s) => s.disableFieldMode);

  useEffect(() => {
    initSyncEngine();
  }, []);

  const handleSync = () => {
    if (isOnline && pendingCount > 0) {
      processSyncQueue();
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => (fieldModeEnabled ? disableFieldMode() : enableFieldMode())}
        className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
          fieldModeEnabled
            ? 'bg-primary-foreground/20 text-primary-foreground'
            : 'bg-primary-foreground/10 text-primary-foreground/70 hover:text-primary-foreground'
        }`}
        data-testid="field-mode-toggle"
        title={fieldModeEnabled ? tField('disableFieldMode') : tField('enableFieldMode')}
      >
        <RadioIcon className="size-3.5" />
        {fieldModeEnabled ? tField('fieldModeEnabled') : tField('fieldModeDisabled')}
      </button>

      <div
        className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-xs ${
          isOnline ? 'text-green-300' : 'text-orange-300'
        }`}
        data-testid="connectivity-status"
      >
        {isOnline ? <WifiIcon className="size-3.5" /> : <WifiOffIcon className="size-3.5" />}
        {isOnline ? t('online') : t('offline')}
      </div>

      {pendingCount > 0 && (
        <button
          onClick={handleSync}
          disabled={!isOnline}
          className="flex items-center gap-1.5 rounded-md bg-primary-foreground/20 px-2.5 py-1 text-xs text-primary-foreground transition-colors hover:bg-primary-foreground/30 disabled:opacity-50"
          data-testid="sync-now-btn"
        >
          <RefreshCwIcon className="size-3.5" />
          {t('pendingCount', { count: pendingCount })}
        </button>
      )}
    </div>
  );
}
