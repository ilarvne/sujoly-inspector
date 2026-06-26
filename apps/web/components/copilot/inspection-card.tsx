'use client';

import { useTranslations } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CalendarIcon, UserIcon } from 'lucide-react';
import type { InspectionRecord } from '@/lib/api/types';
import { STATUS_COLORS_HEX } from '@/lib/constants';

export function InspectionCard({
  data,
  structureName,
}: {
  data: InspectionRecord;
  structureName: string;
}) {
  const t = useTranslations('copilot');
  const tMap = useTranslations('map');

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{structureName}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        <div className="flex items-center gap-1.5">
          <CalendarIcon className="size-3 text-muted-foreground" />
          <span className="text-muted-foreground">{t('date')}:</span>
          <span className="font-medium">{data.date}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <UserIcon className="size-3 text-muted-foreground" />
          <span className="text-muted-foreground">{t('inspector')}:</span>
          <span className="font-medium">{data.inspectorName}</span>
        </div>
        <div>
          <span className="text-muted-foreground">{t('findings')}:</span>
          <p className="mt-0.5 line-clamp-2">{data.findings}</p>
        </div>
        <div className="flex items-center gap-1.5">
          <Badge
            style={{ backgroundColor: STATUS_COLORS_HEX[data.conditionAtInspection] }}
            className="text-white"
          >
            {tMap(`condition.${data.conditionAtInspection}`)}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
