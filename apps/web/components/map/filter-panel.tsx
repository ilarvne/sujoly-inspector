'use client';

import { useState } from 'react';
import { ChevronDownIcon } from 'lucide-react';
import { useTranslations } from 'next-intl';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useFilterStore } from '@/lib/stores/filter-store';
import { mockDistricts, mockBasins } from '@/lib/api/mock-data';
import type { ConditionStatus, InspectionStatus, StructureType } from '@/lib/api/types';

const ALL_VALUE = '__all__';

const conditionOptions: ConditionStatus[] = [
  'normal',
  'inspection',
  'repair',
  'critical',
  'missing',
];
const inspectionStatusOptions: InspectionStatus[] = [
  'current',
  'overdue',
  'due_soon',
  'never',
  'unknown',
];
const typeOptions: StructureType[] = [
  'dam',
  'reservoir',
  'canal',
  'pumping_station',
  'spillway',
  'other',
];

type FilterKey = 'district' | 'basin' | 'type' | 'condition' | 'inspectionStatus';

export function FilterPanel() {
  const t = useTranslations('filter');
  const tMap = useTranslations('map');
  const {
    district,
    basin,
    type,
    condition,
    inspectionStatus,
    setFilter,
    resetFilters,
  } = useFilterStore();
  const [collapsed, setCollapsed] = useState(false);

  const districts = mockDistricts();
  const basins = mockBasins();

  const activeFilterCount = [
    district,
    basin,
    type,
    condition,
    inspectionStatus,
  ].filter((v) => v !== null).length;

  const handleChange = (key: FilterKey, value: string) => {
    setFilter(key, value === ALL_VALUE ? null : value);
  };

  return (
    <div
      data-testid="filter-panel"
      className="absolute top-2 left-2 z-10 w-56 rounded-lg border bg-background/95 p-3 shadow-lg backdrop-blur sm:top-4 sm:left-4 sm:w-64"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold">{t('title')}</h2>
          {activeFilterCount > 0 && (
            <Badge variant="secondary">{activeFilterCount}</Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={t('title')}
        >
          <ChevronDownIcon
            className={`size-4 transition-transform ${collapsed ? '' : 'rotate-180'}`}
          />
        </Button>
      </div>

      {!collapsed && (
        <div className="mt-3 space-y-3">
          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">{t('district')}</span>
            <Select
              value={district ?? ALL_VALUE}
              onValueChange={(v) => handleChange('district', v)}
            >
              <SelectTrigger className="w-full" aria-label={t('district')}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_VALUE}>{t('all')}</SelectItem>
                {districts.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">{t('basin')}</span>
            <Select
              value={basin ?? ALL_VALUE}
              onValueChange={(v) => handleChange('basin', v)}
            >
              <SelectTrigger className="w-full" aria-label={t('basin')}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_VALUE}>{t('all')}</SelectItem>
                {basins.map((b) => (
                  <SelectItem key={b} value={b}>
                    {b}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">{t('type')}</span>
            <Select
              value={type ?? ALL_VALUE}
              onValueChange={(v) => handleChange('type', v)}
            >
              <SelectTrigger className="w-full" aria-label={t('type')}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_VALUE}>{t('all')}</SelectItem>
                {typeOptions.map((tp) => (
                  <SelectItem key={tp} value={tp}>
                    {tMap(`structureType.${tp}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">{t('condition')}</span>
            <Select
              value={condition ?? ALL_VALUE}
              onValueChange={(v) => handleChange('condition', v)}
            >
              <SelectTrigger className="w-full" aria-label={t('condition')}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_VALUE}>{t('all')}</SelectItem>
                {conditionOptions.map((c) => (
                  <SelectItem key={c} value={c}>
                    {tMap(`condition.${c}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">
              {t('inspectionStatus')}
            </span>
            <Select
              value={inspectionStatus ?? ALL_VALUE}
              onValueChange={(v) => handleChange('inspectionStatus', v)}
            >
              <SelectTrigger className="w-full" aria-label={t('inspectionStatus')}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_VALUE}>{t('all')}</SelectItem>
                {inspectionStatusOptions.map((s) => (
                  <SelectItem key={s} value={s}>
                    {tMap(`inspectionStatus.${s}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button
            variant="outline"
            className="w-full"
            onClick={resetFilters}
            disabled={activeFilterCount === 0}
          >
            {t('reset')}
          </Button>
        </div>
      )}
    </div>
  );
}
