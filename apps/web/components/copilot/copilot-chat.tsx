'use client';

import { useRef, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { SparklesIcon, Trash2Icon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useChatStore } from '@/lib/stores/chat-store';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { SuggestedPrompts } from './suggested-prompts';

export function CopilotChat() {
  const t = useTranslations('copilot');
  const locale = useLocale() as 'ru' | 'kk' | 'en';
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const clearChat = useChatStore((s) => s.clearChat);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = (content: string) => {
    sendMessage(content, locale);
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col rounded-xl border bg-background sm:h-[calc(100vh-8rem)] lg:h-[calc(100vh-180px)]">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <SparklesIcon className="size-5 text-primary" />
          <span className="font-display font-semibold">{t('title')}</span>
        </div>
        {!isEmpty && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearChat}
            disabled={isStreaming}
            aria-label={t('clearChat')}
          >
            <Trash2Icon className="size-4" />
            {t('clearChat')}
          </Button>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="space-y-4 p-4">
          {isEmpty ? (
            <div className="space-y-4">
              <div className="rounded-xl bg-muted/50 p-4 text-sm text-muted-foreground">
                {t('welcomeMessage')}
              </div>
              <Separator />
              <SuggestedPrompts onSelect={handleSend} />
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
            </>
          )}
        </div>
      </div>

      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
