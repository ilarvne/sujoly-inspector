'use client';

import { useTranslations } from 'next-intl';
import { Badge } from '@/components/ui/badge';
import { CheckIcon, XIcon } from 'lucide-react';
import type { MatchEvidence } from '@/lib/api/types';

export function EvidenceChip({ evidence }: { evidence: MatchEvidence }) {
  const t = useTranslations('discovery');
  const agreement = evidence.agreement;

  return (
    <Badge
      variant="outline"
      className={agreement ? 'border-green-500/50 text-green-600' : 'border-red-500/50 text-red-600'}
      data-testid={`evidence-${evidence.type}`}
    >
      {agreement ? (
        <CheckIcon className="size-3 text-green-600" />
      ) : (
        <XIcon className="size-3 text-red-600" />
      )}
      <span className="font-medium">{t(`evidence.${evidence.type}`)}</span>
      <span className="text-muted-foreground">: {evidence.value}</span>
    </Badge>
  );
}
