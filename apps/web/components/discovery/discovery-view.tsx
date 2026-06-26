'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useDiscoveryCandidates, useMatchResults } from '@/lib/api/client';
import { CandidateList } from './candidate-list';
import { ComparisonView } from './comparison-view';
import { ReviewActions } from './review-actions';
import type { ReviewStatus } from '@/lib/api/types';

export function DiscoveryView() {
  const t = useTranslations('discovery');
  const { data: candidates } = useDiscoveryCandidates();
  const { data: matches } = useMatchResults();

  const stats = useMemo(() => {
    const total = candidates?.length ?? 0;
    const matchMap = new Map<string, ReviewStatus>();
    if (matches) {
      for (const m of matches) {
        matchMap.set(m.candidateId, m.reviewStatus);
      }
    }
    const pending = candidates?.filter((c) => (matchMap.get(c.id) ?? 'pending') === 'pending').length ?? 0;
    const accepted = candidates?.filter((c) => matchMap.get(c.id) === 'accepted').length ?? 0;
    const linked = candidates?.filter((c) => matchMap.get(c.id) === 'linked').length ?? 0;
    const rejected = candidates?.filter((c) => matchMap.get(c.id) === 'rejected').length ?? 0;
    return { total, pending, accepted, linked, rejected };
  }, [candidates, matches]);

  const statCards = [
    { key: 'total', value: stats.total, color: '#0b4f6c' },
    { key: 'pending', value: stats.pending, color: '#eab308' },
    { key: 'accepted', value: stats.accepted, color: '#22c55e' },
    { key: 'linked', value: stats.linked, color: '#2563eb' },
    { key: 'rejected', value: stats.rejected, color: '#ef4444' },
  ] as const;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {statCards.map((stat) => (
          <Card key={stat.key}>
            <CardContent className="py-3">
              <div className="text-2xl font-bold" style={{ color: stat.color }}>
                {stat.value}
              </div>
              <div className="text-xs text-muted-foreground">
                {t(`stats.${stat.key}`)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t('candidateCount', { count: stats.total })}</CardTitle>
          </CardHeader>
          <CardContent>
            <CandidateList />
          </CardContent>
        </Card>

        <div className="space-y-4">
          <ComparisonView />
          <Card>
            <CardHeader>
              <CardTitle>{t('table.review')}</CardTitle>
            </CardHeader>
            <CardContent>
              <ReviewActions />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
