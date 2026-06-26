'use client';

import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { useTranslations } from 'next-intl';
import type { StructureFeature } from '@/lib/api/types';

interface HeatmapViewProps {
  features: StructureFeature[];
  isLoading: boolean;
}

export function HeatmapView({ features, isLoading }: HeatmapViewProps) {
  const tDash = useTranslations('dashboard');

  const chartData = useMemo(() => {
    const counts = new Map<string, number>();
    for (const f of features) {
      counts.set(f.properties.district, (counts.get(f.properties.district) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([district, count]) => ({ district, count }))
      .sort((a, b) => b.count - a.count);
  }, [features]);

  if (isLoading) {
    return (
      <div className="flex h-[300px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    );
  }

  if (chartData.length === 0) {
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
          dataKey="district"
          tick={{ fontSize: 11 }}
          angle={-20}
          textAnchor="end"
          height={70}
          interval={0}
        />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" fill="#0891b2" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
