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
import { mockRiskScore } from '@/lib/api/mock-data';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, ChevronRight } from 'lucide-react';

export function ObjectsView() {
  const t = useTranslations('objects');
  const tMap = useTranslations('map');
  const locale = useLocale() as keyof TrilingualText;
  const router = useRouter();
  const setSelectedId = useSelectionStore((s) => s.setSelectedId);
  const { data, isLoading } = useStructuresGeoJSON({});
  const [search, setSearch] = useState('');
  const [riskLevel, setRiskLevel] = useState<string>('all');
  const [efficiencyRange, setEfficiencyRange] = useState<string>('all');
  const [ageRange, setAgeRange] = useState<string>('all');

  const currentYear = new Date().getFullYear();

  const features = data?.features ?? [];

  const filtered = useMemo(() => {
    return features.filter((f) => {
      if (search.trim()) {
        const q = search.toLowerCase();
        const name = f.properties.name[locale] || f.properties.name.ru;
        if (!name.toLowerCase().includes(q) && !f.properties.id.toLowerCase().includes(q)) {
          return false;
        }
      }

      if (riskLevel !== 'all') {
        const score = mockRiskScore(f.properties.id).overall;
        if (riskLevel === 'high' && score < 70) return false;
        if (riskLevel === 'medium' && (score < 40 || score >= 70)) return false;
        if (riskLevel === 'low' && score >= 40) return false;
      }

      if (efficiencyRange !== 'all') {
        const eff = f.properties.efficiency?.actual;
        if (eff == null) return false;
        if (efficiencyRange === 'below70' && eff >= 70) return false;
        if (efficiencyRange === '70to85' && (eff < 70 || eff > 85)) return false;
        if (efficiencyRange === 'above85' && eff <= 85) return false;
      }

      if (ageRange !== 'all') {
        const yearBuilt = f.properties.yearBuilt;
        if (yearBuilt == null) return false;
        const age = currentYear - yearBuilt;
        if (ageRange === 'below30' && age >= 30) return false;
        if (ageRange === '30to50' && (age < 30 || age > 50)) return false;
        if (ageRange === 'above50' && age <= 50) return false;
      }

      return true;
    });
  }, [features, search, locale, riskLevel, efficiencyRange, ageRange, currentYear]);

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

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground whitespace-nowrap">{t('riskLevel')}</span>
          <Select value={riskLevel} onValueChange={setRiskLevel}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('all')}</SelectItem>
              <SelectItem value="high">{t('riskHigh')}</SelectItem>
              <SelectItem value="medium">{t('riskMedium')}</SelectItem>
              <SelectItem value="low">{t('riskLow')}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground whitespace-nowrap">{t('efficiency')}</span>
          <Select value={efficiencyRange} onValueChange={setEfficiencyRange}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('all')}</SelectItem>
              <SelectItem value="below70">{t('effBelow70')}</SelectItem>
              <SelectItem value="70to85">{t('eff70to85')}</SelectItem>
              <SelectItem value="above85">{t('effAbove85')}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground whitespace-nowrap">{t('age')}</span>
          <Select value={ageRange} onValueChange={setAgeRange}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t('all')}</SelectItem>
              <SelectItem value="below30">{t('ageBelow30')}</SelectItem>
              <SelectItem value="30to50">{t('age30to50')}</SelectItem>
              <SelectItem value="above50">{t('ageAbove50')}</SelectItem>
            </SelectContent>
          </Select>
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
                    <TableHead className="w-[80px]">{t('efficiency')}</TableHead>
                    <TableHead className="w-[80px]">{t('wear')}</TableHead>
                    <TableHead className="w-[80px]">{t('riskLevel')}</TableHead>
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
                      <TableCell className="text-sm text-muted-foreground">
                        {f.properties.efficiency ? `${f.properties.efficiency.actual}%` : '—'}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {f.properties.wearPercentage != null ? `${f.properties.wearPercentage}%` : '—'}
                      </TableCell>
                      <TableCell>
                        {(() => {
                          const score = mockRiskScore(f.properties.id).overall;
                          const color = score >= 70 ? '#ef4444' : score >= 40 ? '#f97316' : '#22c55e';
                          return (
                            <Badge style={{ backgroundColor: color }} className="text-white text-xs">
                              {score}
                            </Badge>
                          );
                        })()}
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
