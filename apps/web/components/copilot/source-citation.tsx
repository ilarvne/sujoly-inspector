'use client';

import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import { FileTextIcon, DatabaseIcon, MapIcon, FileCheckIcon, AlertTriangleIcon } from 'lucide-react';
import type { CopilotSource } from '@/lib/api/types';
import { useSelectionStore } from '@/lib/stores/selection-store';

const sourceIcons = {
  inspection: FileCheckIcon,
  registry: DatabaseIcon,
  osm: MapIcon,
  document: FileTextIcon,
  risk_assessment: AlertTriangleIcon,
};

const sourceColorClasses = {
  inspection: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
  registry: 'bg-green-100 text-green-800 hover:bg-green-200',
  osm: 'bg-purple-100 text-purple-800 hover:bg-purple-200',
  document: 'bg-amber-100 text-amber-800 hover:bg-amber-200',
  risk_assessment: 'bg-red-100 text-red-800 hover:bg-red-200',
};

const sourceLabelKeys = {
  inspection: 'sourceInspection',
  registry: 'sourceRegistry',
  osm: 'sourceOsm',
  document: 'sourceDocument',
  risk_assessment: 'sourceRisk',
} as const;

export function SourceCitationList({ sources }: { sources: CopilotSource[] }) {
  const t = useTranslations('copilot');
  const router = useRouter();
  const setSelectedId = useSelectionStore((s) => s.setSelectedId);

  if (!sources || sources.length === 0) return null;

  const handleClick = (source: CopilotSource) => {
    if (source.structureId) {
      setSelectedId(source.structureId);
      router.push('/map');
    }
  };

  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">{t('sourcesTitle')}</p>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((source) => {
          const Icon = sourceIcons[source.type];
          const colorClass = sourceColorClasses[source.type];
          const labelKey = sourceLabelKeys[source.type];
          return (
            <button
              key={source.id}
              onClick={() => handleClick(source)}
              className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${colorClass} ${source.structureId ? 'cursor-pointer' : 'cursor-default'}`}
              title={source.reference}
            >
              <Icon className="size-3" />
              <span>{t(labelKey)}</span>
              <span className="opacity-60">[{source.reference}]</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
