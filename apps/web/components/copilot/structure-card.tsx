'use client';

import { useRouter } from 'next/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MapPinIcon, BuildingIcon } from 'lucide-react';
import type { StructureDetail, TrilingualText } from '@/lib/api/types';
import { STATUS_COLORS_HEX } from '@/lib/constants';
import { useSelectionStore } from '@/lib/stores/selection-store';

export function StructureCard({ data }: { data: StructureDetail }) {
  const t = useTranslations('copilot');
  const tMap = useTranslations('map');
  const tPassport = useTranslations('passport');
  const locale = useLocale() as keyof TrilingualText;
  const router = useRouter();
  const setSelectedId = useSelectionStore((s) => s.setSelectedId);

  const name = data.name[locale] || data.name.ru;

  const handleClick = () => {
    setSelectedId(data.id);
    router.push('/map');
  };

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={handleClick}
    >
      <CardHeader>
        <div className="flex items-center gap-2">
          <BuildingIcon className="size-4 text-primary" />
          <CardTitle className="text-sm">{name}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">{tPassport('structureId')}</span>
          <span className="font-medium">{data.id}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">{tPassport('type')}</span>
          <span className="font-medium">{tMap(`structureType.${data.type}`)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-muted-foreground">{tPassport('condition')}</span>
          <Badge
            style={{ backgroundColor: STATUS_COLORS_HEX[data.condition] }}
            className="text-white"
          >
            {tMap(`condition.${data.condition}`)}
          </Badge>
        </div>
        <div className="flex items-center gap-1 text-muted-foreground">
          <MapPinIcon className="size-3" />
          <span>{data.district}</span>
        </div>
      </CardContent>
    </Card>
  );
}
