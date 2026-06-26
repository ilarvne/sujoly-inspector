'use client';

import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useInspections } from '@/lib/api/client';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import { format, parseISO } from 'date-fns';

export function InspectionTimeline({ structureId }: { structureId: string }) {
  const t = useTranslations('inspection');
  const tMap = useTranslations('map');
  const { data: inspections, isLoading } = useInspections(structureId);

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">{t('loading')}</div>;
  }

  if (!inspections || inspections.length === 0) {
    return <div className="p-4 text-muted-foreground">{t('noInspections')}</div>;
  }

  return (
    <ScrollArea className="h-[400px] w-full pr-4">
      <div className="relative space-y-4 pl-6">
        <div className="absolute left-2 top-0 bottom-0 w-px bg-border" />
        {inspections.map((record, index) => (
          <div key={record.id} className="relative space-y-2">
            <div className="absolute -left-[18px] top-1 size-3 rounded-full bg-primary border-2 border-background" />
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">
                {format(parseISO(record.date), 'dd MMM yyyy')}
              </span>
              <Badge
                style={{ backgroundColor: STATUS_COLORS_HEX[record.conditionAtInspection] }}
                className="text-white"
              >
                {tMap(`condition.${record.conditionAtInspection}`)}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground">
              {t('inspector')}: {record.inspectorName}
            </div>
            <p className="text-sm">{record.findings}</p>
            {record.photoUrls.length > 0 && (
              <div className="flex gap-2">
                {record.photoUrls.map((url, i) => (
                  <div
                    key={i}
                    className="size-16 rounded border bg-muted flex items-center justify-center text-xs text-muted-foreground"
                  >
                    Photo {i + 1}
                  </div>
                ))}
              </div>
            )}
            {index < inspections.length - 1 && <Separator className="mt-2" />}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
