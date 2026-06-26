'use client';

import { useMemo } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { Badge } from '@/components/ui/badge';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import { mockStructures, mockRiskScore } from '@/lib/api/mock-data';

export function TopRiskyCard() {
  const locale = useLocale() as 'ru' | 'kk' | 'en';
  const tDash = useTranslations('dashboard');
  const tMap = useTranslations('map');

  const topRisky = useMemo(() => {
    const all = mockStructures().features;
    return all
      .map((f) => {
        const score = mockRiskScore(f.properties.id);
        return { feature: f, score: score.overall };
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);
  }, []);

  function riskColor(score: number): string {
    if (score >= 70) return '#ef4444';
    if (score >= 40) return '#f97316';
    return '#22c55e';
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="max-h-80 overflow-y-auto">
        <ul className="flex flex-col divide-y divide-border">
          {topRisky.map(({ feature, score }) => {
            const { properties } = feature;
            return (
              <li key={properties.id} className="flex items-center justify-between gap-2 py-2">
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{properties.name[locale]}</span>
                  <span className="text-xs text-muted-foreground">
                    {tMap(`structureType.${properties.type}`)} · {properties.district}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge style={{ backgroundColor: riskColor(score), color: '#ffffff' }}>
                    {score}
                  </Badge>
                  <Badge
                    style={{
                      backgroundColor: STATUS_COLORS_HEX[properties.condition],
                      color: '#ffffff',
                    }}
                  >
                    {tMap(`condition.${properties.condition}`)}
                  </Badge>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
      <Link
        href="/map"
        className="text-xs text-primary underline-offset-4 hover:underline"
      >
        {tDash('viewOnMap')}
      </Link>
    </div>
  );
}
