'use client';

import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import type { SyncStatus } from '@/lib/db/types';

const statusColors: Record<SyncStatus, string> = {
  pending: 'bg-yellow-500',
  syncing: 'bg-blue-500',
  confirmed: 'bg-green-500',
  failed: 'bg-red-500',
  conflict: 'bg-orange-500',
};

export function SyncStatusBadge({ status }: { status: SyncStatus }) {
  const t = useTranslations('sync');
  return (
    <Badge
      variant="secondary"
      className={`text-white ${statusColors[status]}`}
      data-testid={`sync-status-${status}`}
    >
      {t(status)}
    </Badge>
  );
}
