'use client';

import { useMemo } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import type { StructureFeature } from '@/lib/api/types';

interface RepairQueueProps {
  features: StructureFeature[];
  isLoading: boolean;
}

export function RepairQueue({ features, isLoading }: RepairQueueProps) {
  const locale = useLocale() as 'ru' | 'kk' | 'en';
  const tDash = useTranslations('dashboard');
  const tMap = useTranslations('map');

  const repairItems = useMemo(
    () =>
      features
        .filter(
          (f) => f.properties.condition === 'critical' || f.properties.condition === 'repair',
        )
        .sort((a, b) => {
          if (a.properties.condition === 'critical' && b.properties.condition !== 'critical')
            return -1;
          if (a.properties.condition !== 'critical' && b.properties.condition === 'critical')
            return 1;
          return 0;
        }),
    [features],
  );

  if (isLoading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    );
  }

  if (repairItems.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-muted-foreground">
        {tDash('noData')}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <span className="text-sm font-medium text-muted-foreground">{repairItems.length}</span>
      <div className="max-h-80 overflow-y-auto">
        <ul className="flex flex-col divide-y divide-border">
          {repairItems.map((f) => {
            const { properties } = f;
            return (
              <li key={properties.id} className="flex items-center justify-between gap-2 py-2">
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{properties.name[locale]}</span>
                  <span className="text-xs text-muted-foreground">
                    {tMap(`structureType.${properties.type}`)} · {properties.district}
                  </span>
                </div>
                <Badge
                  style={{
                    backgroundColor: STATUS_COLORS_HEX[properties.condition],
                    color: '#ffffff',
                  }}
                >
                  {tMap(`condition.${properties.condition}`)}
                </Badge>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
