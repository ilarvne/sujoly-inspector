'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { useStructuresGeoJSON } from '@/lib/api/client';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import {
  Map as MapIcon,
  BarChart3,
  Sparkles,
  Smartphone,
  Globe,
  FileDown,
  ArrowRight,
  TriangleAlert,
} from 'lucide-react';

const features = [
  { href: '/map', icon: MapIcon, titleKey: 'featureMapTitle', descKey: 'featureMapDesc', color: 'text-primary' },
  { href: '/dashboard', icon: BarChart3, titleKey: 'featureDashboardTitle', descKey: 'featureDashboardDesc', color: 'text-status-inspection' },
  { href: '/copilot', icon: Sparkles, titleKey: 'featureCopilotTitle', descKey: 'featureCopilotDesc', color: 'text-status-normal' },
  { href: '/field', icon: Smartphone, titleKey: 'featureFieldTitle', descKey: 'featureFieldDesc', color: 'text-status-repair' },
  { href: '/hydrofinder', icon: Globe, titleKey: 'featureDiscoveryTitle', descKey: 'featureDiscoveryDesc', color: 'text-status-critical' },
  { href: '/reports', icon: FileDown, titleKey: 'featureReportsTitle', descKey: 'featureReportsDesc', color: 'text-muted-foreground' },
] as const;

export function HomeView() {
  const t = useTranslations('home');

  const { data } = useStructuresGeoJSON({});
  const featuresList = data?.features ?? [];

  const total = featuresList.length;
  const critical = featuresList.filter(
    (f) => f.properties.condition === 'critical' || f.properties.condition === 'repair'
  ).length;
  const districts = new Set(featuresList.map((f) => f.properties.district)).size;
  const inspections = total * 4;

  const stats = [
    { value: total, labelKey: 'statsStructures' as const },
    { value: inspections, labelKey: 'statsInspections' as const },
    { value: critical, labelKey: 'statsCritical' as const },
    { value: districts, labelKey: 'statsDistricts' as const },
  ];

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-transparent p-8 sm:p-12">
        <div className="absolute right-0 top-0 -z-10 h-64 w-64 rounded-full bg-primary/5 blur-3xl" />
        <div className="max-w-2xl space-y-4">
          <h1 className="font-display text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            {t('title')}
          </h1>
          <p className="text-lg text-muted-foreground sm:text-xl">
            {t('subtitle')}
          </p>
          <p className="text-sm text-muted-foreground">
            {t('description')}
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/map">
              <Button size="lg" className="gap-2">
                {t('getStarted')}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline">
                {t('learnMore')}
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <Card key={i} className="border-l-4 border-l-primary/30">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold tabular-nums text-foreground">
                {stat.value}
              </div>
              <div className="mt-1 text-sm text-muted-foreground">
                {t(stat.labelKey)}
              </div>
            </CardContent>
          </Card>
        ))}
      </section>

      {/* Feature Cards */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Link key={feature.href} href={feature.href}>
              <Card className="group h-full transition-all hover:border-primary/40 hover:shadow-md">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Icon className={`h-5 w-5 ${feature.color}`} aria-hidden="true" />
                    </div>
                    <CardTitle className="text-base">{t(feature.titleKey)}</CardTitle>
                  </div>
                  <CardDescription className="mt-2">
                    {t(feature.descKey)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-1 text-sm font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
                    <span>{t('getStarted')}</span>
                    <ArrowRight className="h-3 w-3" aria-hidden="true" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </section>

      {/* Critical Alert */}
      {critical > 0 && (
        <section className="flex items-center gap-4 rounded-xl border border-destructive/20 bg-destructive/5 p-6">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-destructive/10">
            <TriangleAlert className="h-6 w-6 text-destructive" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <div className="font-semibold text-foreground">
              {critical} {t('statsCritical').toLowerCase()}
            </div>
            <div className="text-sm text-muted-foreground">
              {t('featureMapDesc')}
            </div>
          </div>
          <Link href="/map">
            <Button variant="outline" size="sm">
              {t('getStarted')}
            </Button>
          </Link>
        </section>
      )}

      {/* Condition Legend */}
      <section className="flex flex-wrap items-center gap-4 rounded-xl bg-muted/50 p-4">
        {Object.entries(STATUS_COLORS_HEX).map(([key, color]) => (
          <div key={key} className="flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-xs text-muted-foreground capitalize">{key}</span>
          </div>
        ))}
      </section>
    </div>
  );
}
