'use client';

import { useTranslations } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertTriangleIcon } from 'lucide-react';
import type { RiskScore } from '@/lib/api/types';

export function RiskBreakdownCard({
  data,
  structureName,
}: {
  data: RiskScore;
  structureName: string;
}) {
  const t = useTranslations('copilot');
  const tRisk = useTranslations('risk');

  const riskLevel = data.overall >= 70 ? 'high' : data.overall >= 40 ? 'medium' : 'low';
  const riskColor = riskLevel === 'high' ? '#ef4444' : riskLevel === 'medium' ? '#f97316' : '#22c55e';

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertTriangleIcon className="size-4 text-primary" />
          <CardTitle className="text-sm">{structureName}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">{t('riskScore')}</span>
          <Badge style={{ backgroundColor: riskColor }} className="text-white">
            {tRisk(riskLevel)}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Progress value={data.overall} className="flex-1" />
          <span className="font-bold">{data.overall}/100</span>
        </div>
        <div className="space-y-1.5">
          {data.components.map((component) => (
            <div key={component.key} className="space-y-0.5">
              <div className="flex justify-between">
                <span className="text-muted-foreground">{tRisk(component.key)}</span>
                <span className="font-medium">{component.score}</span>
              </div>
              <Progress value={component.score} className="h-1.5" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
