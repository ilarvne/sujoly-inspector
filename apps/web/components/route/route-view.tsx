'use client';

import { useState, useMemo } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { mockStructures, mockRiskScore, mockDistricts } from '@/lib/api/mock-data';
import type { TrilingualText } from '@/lib/api/types';
import { RouteMap } from './route-map';

const ALL_VALUE = '__all__';

export interface RouteStop {
  id: string;
  name: TrilingualText;
  riskScore: number;
  lat: number;
  lon: number;
  distanceToNext: number | null;
}

function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function computeRoute(district: string): RouteStop[] {
  const all = mockStructures();

  const valid = all.features.filter((f) => {
    if (!f.geometry) return false;
    const [lon, lat] = f.geometry.coordinates;
    if (lon === 0 && lat === 0) return false;
    if (district !== ALL_VALUE && f.properties.district !== district) return false;
    return true;
  });

  const withRisk = valid.map((f) => {
    const risk = mockRiskScore(f.properties.id);
    const [lon, lat] = f.geometry!.coordinates;
    return {
      id: f.properties.id,
      name: f.properties.name,
      riskScore: risk.overall,
      lat,
      lon,
    };
  });

  const top = withRisk
    .sort((a, b) => b.riskScore - a.riskScore)
    .slice(0, 5);

  if (top.length === 0) return [];

  const ordered: typeof top = [];
  const remaining = [...top];

  while (remaining.length > 0) {
    if (ordered.length === 0) {
      ordered.push(remaining.shift()!);
    } else {
      const current = ordered[ordered.length - 1];
      let nearestIdx = 0;
      let nearestDist = Infinity;
      for (let i = 0; i < remaining.length; i++) {
        const dist = haversineKm(
          current.lat,
          current.lon,
          remaining[i].lat,
          remaining[i].lon,
        );
        if (dist < nearestDist) {
          nearestDist = dist;
          nearestIdx = i;
        }
      }
      ordered.push(remaining.splice(nearestIdx, 1)[0]);
    }
  }

  return ordered.map((stop, idx) => ({
    ...stop,
    distanceToNext:
      idx < ordered.length - 1
        ? haversineKm(
            stop.lat,
            stop.lon,
            ordered[idx + 1].lat,
            ordered[idx + 1].lon,
          )
        : null,
  }));
}

function riskColor(score: number): string {
  if (score >= 70) return '#ef4444';
  if (score >= 40) return '#eab308';
  return '#22c55e';
}

export function RouteView() {
  const t = useTranslations('route');
  const locale = useLocale() as keyof TrilingualText;
  const [district, setDistrict] = useState(ALL_VALUE);
  const [route, setRoute] = useState<RouteStop[] | null>(null);

  const districts = mockDistricts();

  const totalDistance = useMemo(() => {
    if (!route) return 0;
    return route.reduce((sum, s) => sum + (s.distanceToNext ?? 0), 0);
  }, [route]);

  const timeStr = useMemo(() => {
    const totalHours = totalDistance / 50;
    const hours = Math.floor(totalHours);
    const minutes = Math.round((totalHours - hours) * 60);
    return locale === 'en'
      ? `${hours}h ${minutes}min`
      : `${hours} ч ${minutes} мин`;
  }, [totalDistance, locale]);

  const handleGenerate = () => {
    setRoute(computeRoute(district));
  };

  const handleDistrictChange = (value: string) => {
    setDistrict(value);
    setRoute(null);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1 space-y-2">
            <span className="text-sm font-medium">{t('selectDistrict')}</span>
            <Select value={district} onValueChange={handleDistrictChange}>
              <SelectTrigger className="w-full" aria-label={t('selectDistrict')}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_VALUE}>{t('allDistricts')}</SelectItem>
                {districts.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleGenerate} size="lg">
            {t('generateRoute')}
          </Button>
        </CardContent>
      </Card>

      {route !== null &&
        (route.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              {t('noObjects')}
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3">
              <Card>
                <CardContent className="py-3">
                  <div className="text-2xl font-bold text-primary">
                    {totalDistance.toFixed(1)} km
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {t('totalDistance')}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-3">
                  <div className="text-2xl font-bold text-primary">
                    {timeStr}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {t('estimatedTime')}
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1fr]">
              <Card>
                <CardHeader>
                  <CardTitle>{t('routeOrder')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ol className="space-y-3">
                    {route.map((stop, idx) => (
                      <li key={stop.id} className="flex items-center gap-3">
                        <div
                          className="flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white"
                          style={{ backgroundColor: riskColor(stop.riskScore) }}
                        >
                          {idx + 1}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-medium">
                            {stop.name[locale]}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>
                              {t('riskScore')}: {stop.riskScore}
                            </span>
                            {stop.distanceToNext !== null && (
                              <span>
                                {'· '}
                                {stop.distanceToNext.toFixed(1)} km
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex shrink-0 flex-col items-end gap-1">
                          <Badge variant="secondary">{stop.riskScore}</Badge>
                          {idx === 0 && (
                            <span className="text-xs text-muted-foreground">
                              {t('startPoint')}
                            </span>
                          )}
                          {idx === route.length - 1 && (
                            <span className="text-xs text-muted-foreground">
                              {t('endPoint')}
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ol>
                </CardContent>
              </Card>

              <div className="overflow-hidden rounded-lg ring-1 ring-foreground/10">
                <RouteMap
                  stops={route.map((s) => ({ lat: s.lat, lon: s.lon }))}
                />
              </div>
            </div>
          </>
        ))}
    </div>
  );
}
