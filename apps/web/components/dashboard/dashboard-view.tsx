'use client';

import { useTranslations } from 'next-intl';
import { useStructuresGeoJSON } from '@/lib/api/client';
import { useFilterStore } from '@/lib/stores/filter-store';
import { useWeatherStore } from '@/lib/stores/weather-store';
import { mockRiskScore } from '@/lib/api/mock-data';
import { applyWeatherBoost } from '@/lib/utils/weather-risk';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ConditionDonut } from './condition-donut';
import { RepairQueue } from './repair-queue';
import { InspectionStats } from './inspection-stats';
import { HeatmapView } from './heatmap-view';
import { WeatherToggle } from '@/components/weather/weather-toggle';

export function DashboardView() {
  const tDash = useTranslations('dashboard');
  const tWeather = useTranslations('weather');
  const filters = useFilterStore();
  const weatherMode = useWeatherStore((s) => s.mode);
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
