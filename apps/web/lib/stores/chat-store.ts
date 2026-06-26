'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { mockAIEngine } from '@/lib/copilot/mock-ai-engine';
import type { CopilotMessage } from '@/lib/api/types';

type Locale = 'ru' | 'kk' | 'en';

interface ChatState {
  messages: CopilotMessage[];
  isStreaming: boolean;
  _streamInterval: ReturnType<typeof setInterval> | null;
  sendMessage: (content: string, locale: Locale) => void;
  clearChat: () => void;
}

function generateId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      isStreaming: false,
      _streamInterval: null,

      sendMessage: (content: string, locale: Locale) => {
        const trimmed = content.trim();
        if (!trimmed || get().isStreaming) return;

        const userMessage: CopilotMessage = {
          id: generateId(),
          role: 'user',
          content: trimmed,
          timestamp: new Date().toISOString(),
        };

        const assistantId = generateId();
        const assistantPlaceholder: CopilotMessage = {
          id: assistantId,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        };

        set((state) => ({
          messages: [...state.messages, userMessage, assistantPlaceholder],
          isStreaming: true,
        }));

        const response = mockAIEngine(trimmed, locale);
        const words = response.text.split(' ');
        let wordIndex = 0;

        const streamInterval = setInterval(() => {
          wordIndex += 2;
          const partialText = words.slice(0, wordIndex).join(' ');

          set((state) => ({
            messages: state.messages.map((m) =>
              m.id === assistantId
                ? { ...m, content: partialText }
                : m,
            ),
          }));

          if (wordIndex >= words.length) {
            clearInterval(streamInterval);
            set((state) => ({
              _streamInterval: null,
              messages: state.messages.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: response.text,
                      sources: response.sources,
                      cards: response.cards,
                      isStreaming: false,
                    }
                  : m,
              ),
              isStreaming: false,
            }));
          }
        }, 50);

        set({ _streamInterval: streamInterval });
      },

      clearChat: () => {
        const interval = get()._streamInterval;
        if (interval) clearInterval(interval);
        set({ messages: [], isStreaming: false, _streamInterval: null });
      },
    }),
    {
      name: 'sujoly-chat',
      partialize: (state) => ({
        messages: state.messages.map((m) => ({ ...m, isStreaming: false })),
      }),
    },
  ),
);
