'use client';

import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import type { ConfidenceLevel } from '@/lib/api/types';

const confidenceStyles: Record<ConfidenceLevel, { bg: string; text: string }> = {
  high: { bg: '#22c55e', text: 'text-white' },
  medium: { bg: '#eab308', text: 'text-white' },
  low: { bg: '#9ca3af', text: 'text-white' },
};

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const t = useTranslations('discovery');
  const style = confidenceStyles[level];

  return (
    <Badge
      style={{ backgroundColor: style.bg }}
      className={style.text}
      data-testid={`confidence-${level}`}
    >
      {t(`confidence.${level}`)}
    </Badge>
  );
}
