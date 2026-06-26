'use client';

import { useState } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useTranslations, useLocale } from 'next-intl';
import { useSelectionStore } from '@/lib/stores/selection-store';
import { useStructureDetail } from '@/lib/api/client';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import { InspectionTimeline } from '@/components/inspection/inspection-timeline';
import { RiskScoreDisplay } from '@/components/inspection/risk-score-display';
import { DocumentUpload } from '@/components/documents/document-upload';
import { DocumentList } from '@/components/documents/document-list';
import type { TrilingualText } from '@/lib/api/types';
import { cn } from '@/lib/utils';

type TabValue = 'overview' | 'inspections' | 'risk' | 'documents';

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
  const tTabs = useTranslations('passportTabs');
  const [activeTab, setActiveTab] = useState<TabValue>('overview');

  const nameInLocale = (name: TrilingualText) => name[locale] || name.ru;

  const tabs: { value: TabValue; label: string }[] = [
    { value: 'overview', label: tTabs('overview') },
    { value: 'inspections', label: tTabs('inspections') },
    { value: 'risk', label: tTabs('risk') },
    { value: 'documents', label: tTabs('documents') },
  ];

  return (
    <Sheet open={!!selectedId} onOpenChange={(open) => { if (!open) setSelectedId(null); }}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:w-[400px] sm:max-w-[540px]">
        <SheetHeader>
          <SheetTitle>
            {structure ? nameInLocale(structure.name) : t('title')}
          </SheetTitle>
        </SheetHeader>

        {isLoading ? (
          <div className="p-4 text-muted-foreground">{tMap('loading')}</div>
        ) : structure ? (
          <div className="w-full">
            <div role="tablist" className="inline-flex w-full items-center justify-center rounded-lg bg-muted p-[3px] text-muted-foreground h-8">
              {tabs.map((tab) => (
                <button
                  key={tab.value}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab.value}
                  data-state={activeTab === tab.value ? 'active' : 'inactive'}
                  onClick={() => setActiveTab(tab.value)}
                  className={cn(
                    'relative inline-flex flex-1 items-center justify-center rounded-md px-1.5 py-0.5 text-sm font-medium whitespace-nowrap transition-all',
                    activeTab === tab.value
                      ? 'bg-background text-foreground shadow-sm'
                      : 'text-foreground/60 hover:text-foreground'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === 'overview' && (
            <div role="tabpanel" className="space-y-1 px-4 pb-4">
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
            )}

            {activeTab === 'inspections' && (
              <div role="tabpanel" className="px-4 pb-4">
                {structure && <InspectionTimeline structureId={structure.id} />}
              </div>
            )}

            {activeTab === 'risk' && (
              <div role="tabpanel" className="px-4 pb-4">
                {structure && <RiskScoreDisplay structureId={structure.id} />}
              </div>
            )}

            {activeTab === 'documents' && (
              <div role="tabpanel" className="px-4 pb-4 space-y-4">
                {structure && (
                  <>
                    <DocumentUpload structureId={structure.id} />
                    <DocumentList structureId={structure.id} />
                  </>
                )}
              </div>
            )}
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
