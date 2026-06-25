'use client';

import { useTranslations } from 'next-intl';
import { useStructuresGeoJSON } from '@/lib/api/client';
import { useFilterStore } from '@/lib/stores/filter-store';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ConditionDonut } from './condition-donut';
import { RepairQueue } from './repair-queue';
import { InspectionStats } from './inspection-stats';
import { HeatmapView } from './heatmap-view';

export function DashboardView() {
  const tDash = useTranslations('dashboard');
  const filters = useFilterStore();
  const { data, isLoading } = useStructuresGeoJSON(filters);

  const features = data?.features ?? [];

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    );
  }

  if (features.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        {tDash('noData')}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>{tDash('conditionDistribution')}</CardTitle>
        </CardHeader>
        <CardContent>
          <ConditionDonut features={features} isLoading={false} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{tDash('inspectionCoverage')}</CardTitle>
        </CardHeader>
        <CardContent>
          <InspectionStats features={features} isLoading={false} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{tDash('repairQueue')}</CardTitle>
        </CardHeader>
        <CardContent>
          <RepairQueue features={features} isLoading={false} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{tDash('geographicHeatmap')}</CardTitle>
        </CardHeader>
        <CardContent>
          <HeatmapView features={features} isLoading={false} />
        </CardContent>
      </Card>
    </div>
  );
}
