'use client';

import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useTranslations, useLocale } from 'next-intl';
import { useSelectionStore } from '@/lib/stores/selection-store';
import { useStructureDetail } from '@/lib/api/client';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import type { TrilingualText } from '@/lib/api/types';

const sourceLabelKeys = {
  kazvodhoz: 'sourceKazvodhoz',
  osm: 'sourceOsm',
  satellite: 'sourceSatellite',
  manual: 'sourceManual',
} as const;

const confidenceLabelKeys = {
  high: 'confidenceHigh',
  medium: 'confidenceMedium',
  low: 'confidenceLow',
} as const;

export function PassportPanel() {
  const selectedId = useSelectionStore((s) => s.selectedId);
  const setSelectedId = useSelectionStore((s) => s.setSelectedId);
  const { data: structure, isLoading } = useStructureDetail(selectedId);
  const locale = useLocale() as keyof TrilingualText;
  const t = useTranslations('passport');
  const tMap = useTranslations('map');

  const nameInLocale = (name: TrilingualText) => name[locale] || name.ru;

  return (
    <Sheet open={!!selectedId} onOpenChange={(open) => { if (!open) setSelectedId(null); }}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {structure ? nameInLocale(structure.name) : t('title')}
          </SheetTitle>
        </SheetHeader>

        {isLoading ? (
          <div className="p-4 text-muted-foreground">{tMap('loading')}</div>
        ) : structure ? (
          <div className="space-y-1 px-4 pb-4">
            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">{t('identity')}</h3>
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('name')}</dt>
                  <dd className="text-right font-medium">{nameInLocale(structure.name)}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('structureId')}</dt>
                  <dd className="font-medium">{structure.id}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('type')}</dt>
                  <dd className="font-medium">{tMap(`structureType.${structure.type}`)}</dd>
                </div>
              </dl>
            </section>

            <Separator />

            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">{t('geometry')}</h3>
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('coordinates')}</dt>
                  <dd className="font-medium">
                    {structure.coordinates
                      ? `${structure.coordinates.lon.toFixed(4)}, ${structure.coordinates.lat.toFixed(4)}`
                      : '—'}
                  </dd>
                </div>
              </dl>
            </section>

            <Separator />

            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">{t('adminLocation')}</h3>
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('region')}</dt>
                  <dd className="text-right font-medium">{structure.administrativeLocation.region}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('district')}</dt>
                  <dd className="text-right font-medium">{structure.administrativeLocation.district}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('nearestSettlement')}</dt>
                  <dd className="text-right font-medium">{structure.administrativeLocation.nearestSettlement}</dd>
                </div>
              </dl>
            </section>

            <Separator />

            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">{t('technicalSpecs')}</h3>
              <dl className="space-y-1 text-sm">
                {structure.technicalSpecs.height != null && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">{t('height')}</dt>
                    <dd className="font-medium">{structure.technicalSpecs.height} m</dd>
                  </div>
                )}
                {structure.technicalSpecs.length != null && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">{t('length')}</dt>
                    <dd className="font-medium">{structure.technicalSpecs.length} m</dd>
                  </div>
                )}
                {structure.technicalSpecs.capacity != null && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">{t('capacity')}</dt>
                    <dd className="font-medium">{structure.technicalSpecs.capacity} Mm³</dd>
                  </div>
                )}
                {structure.technicalSpecs.yearBuilt != null && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">{t('yearBuilt')}</dt>
                    <dd className="font-medium">{structure.technicalSpecs.yearBuilt}</dd>
                  </div>
                )}
                {structure.technicalSpecs.designType && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">{t('designType')}</dt>
                    <dd className="text-right font-medium">{structure.technicalSpecs.designType}</dd>
                  </div>
                )}
                {structure.technicalSpecs.materials && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">{t('materials')}</dt>
                    <dd className="text-right font-medium">{structure.technicalSpecs.materials}</dd>
                  </div>
                )}
              </dl>
            </section>

            <Separator />

            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">{t('status')}</h3>
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between gap-4 items-center">
                  <dt className="text-muted-foreground">{t('condition')}</dt>
                  <dd>
                    <Badge
                      style={{ backgroundColor: STATUS_COLORS_HEX[structure.condition] }}
                      className="text-white"
                    >
                      {tMap(`condition.${structure.condition}`)}
                    </Badge>
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('inspectionStatus')}</dt>
                  <dd className="text-right font-medium">{tMap(`inspectionStatus.${structure.inspectionStatus}`)}</dd>
                </div>
              </dl>
            </section>

            <Separator />

            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">{t('provenance')}</h3>
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('source')}</dt>
                  <dd className="text-right font-medium">
                    {t(sourceLabelKeys[structure.provenance.source as keyof typeof sourceLabelKeys] ?? 'source')}
                  </dd>
                </div>
                <div className="flex justify-between gap-4 items-center">
                  <dt className="text-muted-foreground">{t('confidence')}</dt>
                  <dd>
                    <Badge variant="secondary">
                      {t(confidenceLabelKeys[structure.provenance.confidence])}
                    </Badge>
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t('lastVerified')}</dt>
                  <dd className="font-medium">{structure.provenance.lastVerified}</dd>
                </div>
              </dl>
            </section>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
