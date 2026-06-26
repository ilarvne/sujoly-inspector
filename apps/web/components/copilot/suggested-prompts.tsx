'use client';

import { useLocale } from 'next-intl';
import { useTranslations } from 'next-intl';
import { MessageSquareIcon } from 'lucide-react';
import { getSuggestedPrompts } from '@/lib/copilot/mock-ai-engine';

export function SuggestedPrompts({
  onSelect,
}: {
  onSelect: (prompt: string) => void;
}) {
  const locale = useLocale() as 'ru' | 'kk' | 'en';
  const t = useTranslations('copilot');
  const prompts = getSuggestedPrompts(locale);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <MessageSquareIcon className="size-4" />
        {t('suggestedPrompts')}
      </div>
      <div className="flex flex-col gap-2">
        {prompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => onSelect(prompt)}
            className="rounded-lg border border-border bg-card px-4 py-2.5 text-left text-sm transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
