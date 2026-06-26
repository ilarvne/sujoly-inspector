'use client';

import { useTranslations } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { FileTextIcon } from 'lucide-react';
import type { CopilotCard } from '@/lib/api/types';

export function ReportCard({ data }: { data: Extract<CopilotCard, { type: 'report' }>['data'] }) {
  const t = useTranslations('copilot');

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileTextIcon className="size-4 text-primary" />
          <CardTitle className="text-sm">{data.title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        <p className="line-clamp-3 text-muted-foreground">{data.summary}</p>
        <div className="flex items-center justify-between border-t pt-2">
          <span className="text-muted-foreground">{t('totalStructures')}</span>
          <span className="font-bold">{data.structureCount}</span>
        </div>
      </CardContent>
    </Card>
  );
}
