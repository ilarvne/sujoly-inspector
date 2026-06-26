'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { TriangleAlertIcon, LayersIcon } from 'lucide-react';
import { useStructuresGeoJSON } from '@/lib/api/client';
import { useFilterStore } from '@/lib/stores/filter-store';
import { useWeatherStore } from '@/lib/stores/weather-store';
import { mockRiskScore, mockStructures, detectDuplicateStructures } from '@/lib/api/mock-data';
import { applyWeatherBoost } from '@/lib/utils/weather-risk';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ConditionDonut } from './condition-donut';
import { RepairQueue } from './repair-queue';
import { InspectionStats } from './inspection-stats';
import { HeatmapView } from './heatmap-view';
import { TopRiskyCard } from './top-risky-card';
import { TypeAnalytics } from './type-analytics';
import { WeatherToggle } from '@/components/weather/weather-toggle';

export function DashboardView() {
  const tDash = useTranslations('dashboard');
  const tWeather = useTranslations('weather');
  const filters = useFilterStore();
  const weatherMode = useWeatherStore((s) => s.mode);
  const { data, isLoading } = useStructuresGeoJSON(filters);

  const features = data?.features ?? [];

  const { missingCoordsCount, duplicateCount } = useMemo(() => {
    const allFeatures = mockStructures().features;
    const missing = allFeatures.filter(
      (f) =>
        f.geometry === null ||
        (f.geometry.coordinates[0] === 0 && f.geometry.coordinates[1] === 0),
    ).length;
    const dups = detectDuplicateStructures().length;
    return { missingCoordsCount: missing, duplicateCount: dups };
  }, []);

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

  const avgRiskScore = (() => {
    const scores = features.map((f) => {
      const base = mockRiskScore(f.properties.id);
      return weatherMode !== 'normal'
        ? applyWeatherBoost(f.properties.id, base, weatherMode).overall
        : base.overall;
    });
    return scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
  })();

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3">
        <WeatherToggle />
        {weatherMode !== 'normal' && (
          <div className="rounded-lg bg-yellow-100 p-3 text-sm font-medium text-yellow-900 dark:bg-yellow-900/30 dark:text-yellow-100">
            {tWeather('boostActive')}
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{tWeather('averageRisk')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">{avgRiskScore}</span>
              <span className="text-sm text-muted-foreground">/ 100</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{tDash('conditionDistribution')}</CardTitle>
          </CardHeader>
          <CardContent>
            <ConditionDonut features={features} isLoading={false} />
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent className="flex items-center gap-3 py-4">
            <TriangleAlertIcon className="size-8 shrink-0 text-yellow-500" />
            <div className="flex flex-col">
              <span className="text-2xl font-bold text-primary">{missingCoordsCount}</span>
              <span className="text-xs text-muted-foreground">{tDash('missingCoords')}</span>
            </div>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardContent className="flex items-center gap-3 py-4">
            <LayersIcon className="size-8 shrink-0 text-blue-500" />
            <div className="flex flex-col">
              <span className="text-2xl font-bold text-primary">{duplicateCount}</span>
              <span className="text-xs text-muted-foreground">{tDash('duplicates')}</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{tDash('topRisky')}</CardTitle>
          </CardHeader>
          <CardContent>
            <TopRiskyCard />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{tDash('byType')}</CardTitle>
          </CardHeader>
          <CardContent>
            <TypeAnalytics features={features} isLoading={false} />
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
    </div>
  );
}
