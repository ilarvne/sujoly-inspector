'use client';

import { useTranslations } from 'next-intl';
import { UserIcon, SparklesIcon } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import type { CopilotMessage, CopilotCard } from '@/lib/api/types';
import { SourceCitationList } from './source-citation';
import { StructureCard } from './structure-card';
import { RiskBreakdownCard } from './risk-breakdown-card';
import { InspectionCard } from './inspection-card';
import { ReportCard } from './report-card';

function renderCard(card: CopilotCard) {
  switch (card.type) {
    case 'structure':
      return <StructureCard key={`s-${card.data.id}`} data={card.data} />;
    case 'risk':
      return (
        <RiskBreakdownCard
          key={`r-${card.structureId}`}
          data={card.data}
          structureName={card.structureName}
        />
      );
    case 'inspection':
      return (
        <InspectionCard
          key={`i-${card.data.id}`}
          data={card.data}
          structureName={card.structureName}
        />
      );
    case 'report':
      return <ReportCard key={`rep-${card.data.title}`} data={card.data} />;
    default:
      return null;
  }
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

export function ChatMessage({ message }: { message: CopilotMessage }) {
  const t = useTranslations('copilot');
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <Avatar className="size-8 shrink-0">
        <AvatarFallback className={isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'}>
          {isUser ? <UserIcon className="size-4" /> : <SparklesIcon className="size-4" />}
        </AvatarFallback>
      </Avatar>

      <div className={`flex max-w-[80%] flex-col gap-2 ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm ${
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-card ring-1 ring-border'
          }`}
        >
          {message.isStreaming && !message.content ? (
            <div className="flex items-center gap-1.5">
              <span className="size-2 animate-pulse rounded-full bg-muted-foreground/50" />
              <span className="size-2 animate-pulse rounded-full bg-muted-foreground/50 [animation-delay:150ms]" />
              <span className="size-2 animate-pulse rounded-full bg-muted-foreground/50 [animation-delay:300ms]" />
              <span className="text-xs text-muted-foreground">{t('streaming')}</span>
            </div>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {message.cards && message.cards.length > 0 && !message.isStreaming && (
          <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
            {message.cards.map((card) => renderCard(card))}
          </div>
        )}

        {message.sources && message.sources.length > 0 && !message.isStreaming && (
          <div className="w-full">
            <SourceCitationList sources={message.sources} />
          </div>
        )}

        {!message.isStreaming && (
          <span className="text-xs text-muted-foreground">
            {formatTimestamp(message.timestamp)}
          </span>
        )}
      </div>
    </div>
  );
}
