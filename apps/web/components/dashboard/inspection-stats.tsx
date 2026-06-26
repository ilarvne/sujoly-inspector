'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Card, CardContent } from '@/components/ui/card';
import type { StructureFeature } from '@/lib/api/types';

interface InspectionStatsProps {
  features: StructureFeature[];
  isLoading: boolean;
}

export function InspectionStats({ features, isLoading }: InspectionStatsProps) {
  const tDash = useTranslations('dashboard');

  const { totalStructures, needsInspection, coverageRate } = useMemo(() => {
    const totalStructures = features.length;
    const needsInspection = features.filter(
      (f) =>
        f.properties.inspectionStatus === 'overdue' ||
        f.properties.inspectionStatus === 'due_soon' ||
        f.properties.inspectionStatus === 'never',
    ).length;
    const coverageRate =
      totalStructures > 0
        ? Math.round(
            (features.filter((f) => f.properties.inspectionStatus === 'current').length /
              totalStructures) *
              100,
          )
        : 0;
    return { totalStructures, needsInspection, coverageRate };
  }, [features]);

  if (isLoading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    );
  }

  const stats = [
    { label: tDash('totalStructures'), value: String(totalStructures) },
    { label: tDash('needsInspection'), value: String(needsInspection) },
    { label: tDash('coverageRate'), value: `${coverageRate}%` },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {stats.map((stat) => (
        <Card key={stat.label} size="sm">
          <CardContent className="flex flex-col items-center py-4 text-center">
            <span className="text-2xl font-bold text-primary">{stat.value}</span>
            <span className="mt-1 text-xs text-muted-foreground">{stat.label}</span>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
