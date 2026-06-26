'use client';

import { useTranslations } from 'next-intl';
import { useRiskScore } from '@/lib/api/client';

export function RiskScoreDisplay({ structureId }: { structureId: string }) {
  const t = useTranslations('risk');
  const { data: riskScore, isLoading } = useRiskScore(structureId);

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">{t('loading')}</div>;
  }

  if (!riskScore) {
    return null;
  }

  const level = riskScore.overall >= 70 ? 'high' : riskScore.overall >= 40 ? 'medium' : 'low';

  return (
    <div className="space-y-4">
      <div>
        <div className="text-4xl font-bold text-primary">{riskScore.overall}</div>
        <div className="text-sm text-muted-foreground">
          {t('riskLevel')}: {t(level)}
        </div>
      </div>
      <p className="text-sm">{riskScore.explanation}</p>
    </div>
  );
}
