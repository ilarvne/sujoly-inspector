'use client';

import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { useTranslations } from 'next-intl';
import type { StructureFeature, StructureType } from '@/lib/api/types';

interface TypeAnalyticsProps {
  features: StructureFeature[];
  isLoading: boolean;
}

const STRUCTURE_TYPES: StructureType[] = [
  'dam',
  'reservoir',
  'canal',
  'pumping_station',
  'spillway',
  'other',
];

export function TypeAnalytics({ features, isLoading }: TypeAnalyticsProps) {
  const tDash = useTranslations('dashboard');
  const tMap = useTranslations('map');

  const chartData = useMemo(
    () =>
      STRUCTURE_TYPES.map((type) => ({
        type: tMap(`structureType.${type}`),
        count: features.filter((f) => f.properties.type === type).length,
      })),
    [features, tMap],
  );

  if (isLoading) {
    return (
      <div className="flex h-[300px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    );
  }

  if (features.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
        {tDash('noData')}
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <XAxis
          dataKey="type"
          tick={{ fontSize: 11 }}
          angle={-20}
          textAnchor="end"
          height={70}
          interval={0}
        />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
