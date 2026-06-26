'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { useRiskScore } from '@/lib/api/client';
import { useAuthStore } from '@/lib/stores/auth-store';
import { EngineerOverrideDialog } from '@/components/override/engineer-override-dialog';

export function RiskScoreDisplay({ structureId }: { structureId: string }) {
  const t = useTranslations('risk');
  const tOverride = useTranslations('override');
  const { data: riskScore, isLoading } = useRiskScore(structureId);
  const hasRole = useAuthStore((s) => s.hasRole);
  const [overrideOpen, setOverrideOpen] = useState(false);

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">{t('loading')}</div>;
  }

  if (!riskScore) {
    return null;
  }

  const riskLevel = riskScore.overall >= 70 ? 'high' : riskScore.overall >= 40 ? 'medium' : 'low';
  const riskColor = riskLevel === 'high' ? '#ef4444' : riskLevel === 'medium' ? '#f97316' : '#22c55e';
  const canOverride = hasRole('admin', 'engineer');

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">{t('overallScore')}</span>
          <Badge style={{ backgroundColor: riskColor }} className="text-white">
            {t(riskLevel)}
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          <Progress value={riskScore.overall} className="flex-1" />
          <span className="text-lg font-bold">{riskScore.overall}</span>
        </div>
      </div>

      <Separator />

      <div className="space-y-2">
        <h3 className="text-sm font-semibold">{t('componentBreakdown')}</h3>
        <Accordion type="single" collapsible>
          {riskScore.components.map((component) => (
            <AccordionItem key={component.key} value={component.key}>
              <AccordionTrigger className="text-sm">
                <div className="flex w-full items-center justify-between pr-2">
                  <span>{t(component.key)}</span>
                  <span className="text-xs text-muted-foreground">{component.score}/100</span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="space-y-2">
                <Progress value={component.score} />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{t('weight')}: {(component.weight * 100).toFixed(0)}%</span>
                  <span>{t('score')}: {component.score}</span>
                </div>
                <p className="text-xs">{component.description}</p>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>

      <Separator />

      <div className="space-y-1">
        <h3 className="text-sm font-semibold">{t('explanation')}</h3>
        <p className="text-sm text-muted-foreground">{riskScore.explanation}</p>
        <p className="text-xs text-muted-foreground">{t('computedAt')}: {riskScore.computedAt}</p>
      </div>

      {canOverride && (
        <>
          <Separator />
          <Button onClick={() => setOverrideOpen(true)} className="w-full">
            {tOverride('title')}
          </Button>
          <EngineerOverrideDialog
            structureId={structureId}
            open={overrideOpen}
            onOpenChange={setOverrideOpen}
          />
        </>
      )}
    </div>
  );
}
