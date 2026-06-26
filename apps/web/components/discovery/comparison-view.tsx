'use client';

import { useTranslations, useLocale } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useDiscoveryCandidate, useMatchResult, useStructureDetail } from '@/lib/api/client';
import { EvidenceChip } from './evidence-chip';
import { SourceChip } from './source-chip';
import { ConfidenceBadge } from './confidence-badge';
import { useDiscoveryStore } from '@/lib/stores/discovery-store';

function FieldRow({ label, existing, candidate }: { label: string; existing?: string | null; candidate?: string | null }) {
  const isDiff = existing !== candidate;
  return (
    <div className="grid grid-cols-[120px_1fr_1fr] gap-2 py-1.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={isDiff && existing ? 'font-medium' : ''}>{existing ?? '—'}</span>
      <span className={isDiff && candidate ? 'font-medium text-primary' : ''}>{candidate ?? '—'}</span>
    </div>
  );
}

export function ComparisonView() {
  const t = useTranslations('discovery');
  const locale = useLocale() as 'ru' | 'kk' | 'en';
  const { selectedCandidateId } = useDiscoveryStore();

  const { data: candidate } = useDiscoveryCandidate(selectedCandidateId);
  const { data: match } = useMatchResult(selectedCandidateId);
  const { data: existing } = useStructureDetail(match?.existingStructureId ?? null);

  if (!selectedCandidateId || !candidate) {
    return (
      <Card>
        <CardContent className="flex h-48 items-center justify-center text-muted-foreground">
          {t('comparison.selectCandidate')}
        </CardContent>
      </Card>
    );
  }

  const existingName = existing ? existing.name[locale] : null;
  const candidateName = candidate.name[locale];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{t('comparison.title')}</CardTitle>
          <SourceChip source={candidate.source} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">{t('comparison.matchScore')}</span>
            {match && (
              <span className={`text-lg font-bold ${match.matchScore >= 70 ? 'text-green-600' : match.matchScore >= 40 ? 'text-yellow-600' : 'text-muted-foreground'}`}>
                {match.matchScore}%
              </span>
            )}
          </div>
          {match && <Progress value={match.matchScore} />}
        </div>

        <Separator />

        <div className="grid grid-cols-[120px_1fr_1fr] gap-2 text-xs font-semibold text-muted-foreground pb-1">
          <span></span>
          <span>{t('comparison.existingRecord')}</span>
          <span>{t('comparison.candidateRecord')}</span>
        </div>

        {match?.existingStructureId && existing ? (
          <ScrollArea className="h-[280px] pr-4">
            <FieldRow
              label={t('comparison.name')}
              existing={existingName}
              candidate={candidateName}
            />
            <FieldRow
              label={t('comparison.type')}
              existing={t(`structureType.${existing.type}`)}
              candidate={t(`structureType.${candidate.type}`)}
            />
            <FieldRow
              label={t('comparison.coordinates')}
              existing={existing.coordinates ? `${existing.coordinates.lon.toFixed(4)}, ${existing.coordinates.lat.toFixed(4)}` : '—'}
              candidate={candidate.coordinates ? `${candidate.coordinates.lon.toFixed(4)}, ${candidate.coordinates.lat.toFixed(4)}` : '—'}
            />
            <FieldRow
              label={t('comparison.district')}
              existing={existing.district}
              candidate={candidate.district}
            />
            <FieldRow
              label={t('comparison.basin')}
              existing={existing.basin}
              candidate={candidate.basin}
            />
            <FieldRow
              label={t('comparison.height')}
              existing={existing.technicalSpecs.height ? `${existing.technicalSpecs.height} m` : '—'}
              candidate={candidate.properties.height ? `${candidate.properties.height} m` : '—'}
            />
            <FieldRow
              label={t('comparison.length')}
              existing={existing.technicalSpecs.length ? `${existing.technicalSpecs.length} m` : '—'}
              candidate={candidate.properties.length ? `${candidate.properties.length} m` : '—'}
            />
            <FieldRow
              label={t('comparison.yearBuilt')}
              existing={existing.technicalSpecs.yearBuilt?.toString() ?? '—'}
              candidate={candidate.properties.yearBuilt?.toString() ?? '—'}
            />
          </ScrollArea>
        ) : (
          <div className="flex h-32 items-center justify-center text-muted-foreground">
            {t('comparison.noMatch')}
          </div>
        )}

        {match && match.evidence.length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">{t('comparison.evidence')}</h4>
              <div className="flex flex-wrap gap-2">
                {match.evidence.map((ev, i) => (
                  <EvidenceChip key={i} evidence={ev} />
                ))}
              </div>
            </div>
          </>
        )}

        <Separator />

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{t('comparison.detectedAt')}: {candidate.detectedAt}</span>
          <ConfidenceBadge level={candidate.confidence} />
        </div>
      </CardContent>
    </Card>
  );
}
