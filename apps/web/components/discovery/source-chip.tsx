'use client';

import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import { SatelliteIcon, MapIcon, FileTextIcon, PencilIcon } from 'lucide-react';
import type { DiscoverySource } from '@/lib/api/types';

const sourceIcons: Record<DiscoverySource, React.ComponentType<{ className?: string }>> = {
  osm: MapIcon,
  satellite: SatelliteIcon,
  kazvodhoz: FileTextIcon,
  manual: PencilIcon,
};

const sourceColors: Record<DiscoverySource, string> = {
  osm: '#0b4f6c',
  satellite: '#7c3aed',
  kazvodhoz: '#2563eb',
  manual: '#6b7280',
};

export function SourceChip({ source }: { source: DiscoverySource }) {
  const t = useTranslations('discovery');
  const Icon = sourceIcons[source];

  return (
    <Badge
      variant="outline"
      style={{ borderColor: sourceColors[source], color: sourceColors[source] }}
      className="gap-1"
      data-testid={`source-${source}`}
    >
      <Icon className="size-3" />
      {t(`sources.${source}`)}
    </Badge>
  );
}
