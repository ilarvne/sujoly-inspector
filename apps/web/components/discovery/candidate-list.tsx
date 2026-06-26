'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { SearchIcon } from 'lucide-react';
import { useDiscoveryCandidates, useMatchResults } from '@/lib/api/client';
import { useDiscoveryStore } from '@/lib/stores/discovery-store';
import { ConfidenceBadge } from './confidence-badge';
import { SourceChip } from './source-chip';
import type { ReviewStatus } from '@/lib/api/types';

const statusColors: Record<ReviewStatus, string> = {
  pending: '#eab308',
  accepted: '#22c55e',
  linked: '#2563eb',
  rejected: '#ef4444',
};

export function CandidateList() {
  const t = useTranslations('discovery');
  const locale = useLocale() as 'ru' | 'kk' | 'en';
  const { data: candidates, isLoading } = useDiscoveryCandidates();
  const { data: matchResults } = useMatchResults();
  const { selectedCandidateId, reviewFilter, searchQuery, setSelectedCandidate } = useDiscoveryStore();

  const matchMap = useMemo(() => {
    const map = new Map<string, typeof matchResults extends (infer T)[] | undefined ? T : never>();
    if (matchResults) {
      for (const m of matchResults) {
        map.set(m.candidateId, m);
      }
    }
    return map;
  }, [matchResults]);

  const filtered = useMemo(() => {
    if (!candidates) return [];
    return candidates.filter((c) => {
      const match = matchMap.get(c.id);
      const status = match?.reviewStatus ?? 'pending';
      if (reviewFilter !== 'all' && status !== reviewFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const name = c.name[locale].toLowerCase();
        if (!name.includes(q)) return false;
      }
      return true;
    });
  }, [candidates, matchMap, reviewFilter, searchQuery, locale]);

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">{t('loading')}</div>;
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <SearchIcon className="absolute left-2 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t('filter.search')}
            value={searchQuery}
            onChange={(e) => useDiscoveryStore.getState().setSearchQuery(e.target.value)}
            className="pl-8"
            data-testid="discovery-search"
          />
        </div>
        <Select
          value={reviewFilter}
          onValueChange={(v) => useDiscoveryStore.getState().setReviewFilter(v as ReviewStatus | 'all')}
        >
          <SelectTrigger className="w-[140px]" data-testid="discovery-filter">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('filter.all')}</SelectItem>
            <SelectItem value="pending">{t('filter.pending')}</SelectItem>
            <SelectItem value="accepted">{t('filter.accepted')}</SelectItem>
            <SelectItem value="linked">{t('filter.linked')}</SelectItem>
            <SelectItem value="rejected">{t('filter.rejected')}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {filtered.length === 0 ? (
        <div className="flex h-32 items-center justify-center text-muted-foreground">
          {t('noCandidates')}
        </div>
      ) : (
        <ScrollArea className="h-[400px] rounded-md border lg:h-[500px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[120px]">{t('table.source')}</TableHead>
                <TableHead>{t('table.name')}</TableHead>
                <TableHead className="w-[100px]">{t('table.type')}</TableHead>
                <TableHead className="w-[90px]">{t('table.confidence')}</TableHead>
                <TableHead className="w-[70px]">{t('table.matchScore')}</TableHead>
                <TableHead className="w-[90px]">{t('table.status')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((cand) => {
                const match = matchMap.get(cand.id);
                const status = match?.reviewStatus ?? 'pending';
                const isSelected = selectedCandidateId === cand.id;
                return (
                  <TableRow
                    key={cand.id}
                    onClick={() => setSelectedCandidate(cand.id)}
                    className={`cursor-pointer transition-colors ${isSelected ? 'bg-primary/10 font-medium' : 'hover:bg-muted/50'}`}
                    data-testid={`candidate-row-${cand.id}`}
                  >
                    <TableCell>
                      <SourceChip source={cand.source} />
                    </TableCell>
                    <TableCell className="font-medium">
                      {cand.name[locale]}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {t(`structureType.${cand.type}`)}
                    </TableCell>
                    <TableCell>
                      <ConfidenceBadge level={cand.confidence} />
                    </TableCell>
                    <TableCell>
                      {match ? (
                        <span className={match.matchScore >= 70 ? 'font-semibold text-green-600' : match.matchScore >= 40 ? 'font-semibold text-yellow-600' : 'text-muted-foreground'}>
                          {match.matchScore}%
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        style={{ backgroundColor: statusColors[status] }}
                        className="text-white"
                      >
                        {t(`review.${status}`)}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </ScrollArea>
      )}
    </div>
  );
}
