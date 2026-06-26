'use client';

import { useRef, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { SparklesIcon, Trash2Icon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
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
    const viewport = document.querySelector('[data-radix-scroll-area-viewport]');
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    } else if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSend = (content: string) => {
    sendMessage(content, locale);
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-180px)] flex-col rounded-xl border bg-background">
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

      <ScrollArea className="flex-1" >
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
              <div ref={scrollRef} />
            </>
          )}
        </div>
      </ScrollArea>

      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
