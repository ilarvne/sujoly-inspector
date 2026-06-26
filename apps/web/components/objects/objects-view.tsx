'use client';

import { useState, useMemo } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter } from '@/i18n/navigation';
import { useStructuresGeoJSON } from '@/lib/api/client';
import { useSelectionStore } from '@/lib/stores/selection-store';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import type { TrilingualText } from '@/lib/api/types';
import { Search, ChevronRight } from 'lucide-react';

export function ObjectsView() {
  const t = useTranslations('objects');
  const tMap = useTranslations('map');
  const locale = useLocale() as keyof TrilingualText;
  const router = useRouter();
  const setSelectedId = useSelectionStore((s) => s.setSelectedId);
  const { data, isLoading } = useStructuresGeoJSON({});
  const [search, setSearch] = useState('');

  const features = data?.features ?? [];

  const filtered = useMemo(() => {
    if (!search.trim()) return features;
    const q = search.toLowerCase();
    return features.filter((f) => {
      const name = f.properties.name[locale] || f.properties.name.ru;
      return name.toLowerCase().includes(q) || f.properties.id.toLowerCase().includes(q);
    });
  }, [features, search, locale]);

  const nameInLocale = (name: TrilingualText) => name[locale] || name.ru;

  const handleRowClick = (id: string) => {
    setSelectedId(id);
    router.push('/map');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <div>
          <h1 className="font-display text-xl font-bold text-foreground sm:text-2xl">{t('title')}</h1>
          <p className="text-sm text-muted-foreground">{t('subtitle')}</p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('search')}
            className="pl-9"
            aria-label={t('search')}
          />
        </div>
      </div>

      <div className="text-sm text-muted-foreground">
        {t('resultsCount', { count: filtered.length })}
      </div>

      {isLoading ? (
        <div className="flex h-32 items-center justify-center text-muted-foreground">
          {t('loading')}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex h-32 items-center justify-center text-muted-foreground">
          {t('noResults')}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[60px]">{t('colId')}</TableHead>
                    <TableHead>{t('colName')}</TableHead>
                    <TableHead className="w-[120px]">{t('colType')}</TableHead>
                    <TableHead className="w-[140px]">{t('colDistrict')}</TableHead>
                    <TableHead className="w-[140px]">{t('colCondition')}</TableHead>
                    <TableHead className="w-[120px]">{t('colInspection')}</TableHead>
                    <TableHead className="w-[80px]">{t('colYear')}</TableHead>
                    <TableHead className="w-[50px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((f) => (
                    <TableRow
                      key={f.properties.id}
                      onClick={() => handleRowClick(f.properties.id)}
                      className="cursor-pointer transition-colors hover:bg-muted/50"
                    >
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {f.properties.id}
                      </TableCell>
                      <TableCell className="font-medium">
                        {nameInLocale(f.properties.name)}
                      </TableCell>
                      <TableCell className="text-sm">
                        {tMap(`structureType.${f.properties.type}`)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {f.properties.district}
                      </TableCell>
                      <TableCell>
                        <Badge
                          style={{ backgroundColor: STATUS_COLORS_HEX[f.properties.condition] }}
                          className="text-white text-xs"
                        >
                          {tMap(`condition.${f.properties.condition}`)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {tMap(`inspectionStatus.${f.properties.inspectionStatus}`)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {f.properties.yearBuilt ?? '—'}
                      </TableCell>
                      <TableCell>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
