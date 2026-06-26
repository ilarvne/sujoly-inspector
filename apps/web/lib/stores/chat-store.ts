'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CopilotMessage, CopilotSource, CopilotSourceType } from '@/lib/api/types';

type Locale = 'ru' | 'kk' | 'en';

// ---------------------------------------------------------------------------
// Backend configuration & auth (mirrors lib/api/client.ts)
// ---------------------------------------------------------------------------

const API_BASE_URL = 'http://localhost:8000/api/v1';
const API_KEY = 'dev-admin-key';

let cachedToken: string | null = null;

async function getToken(): Promise<string> {
  if (cachedToken) return cachedToken;
  const res = await fetch(`${API_BASE_URL}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: API_KEY }),
  });
  if (!res.ok) throw new Error('Failed to get auth token');
  const data = await res.json();
  cachedToken = data.access_token as string;
  return cachedToken!;
}

// ---------------------------------------------------------------------------
// Copilot API response shape
// ---------------------------------------------------------------------------

interface CopilotEvidenceItem {
  source_type: string;
  source_id: string;
  relevance: number;
  snippet?: string;
}

interface CopilotApiResponse {
  message: string;
  requires_confirmation: boolean;
  confirmation_type: string | null;
  evidence: CopilotEvidenceItem[];
  suggestions: string[];
  conversation_id: string;
}

// ---------------------------------------------------------------------------
// Mapping helpers
// ---------------------------------------------------------------------------

function mapEvidenceType(sourceType: string): CopilotSourceType {
  switch (sourceType) {
    case 'inspection':
      return 'inspection';
    case 'document':
      return 'document';
    case 'risk_assessment':
      return 'risk_assessment';
    default:
      return 'registry';
  }
}

function mapEvidenceToSources(
  evidence: CopilotEvidenceItem[],
): CopilotSource[] {
  return (evidence || []).map((e, i) => ({
    id: `src-${i}-${e.source_id.slice(0, 8)}`,
    type: mapEvidenceType(e.source_type),
    label: e.snippet || `${e.source_type} ${e.source_id.slice(0, 8)}`,
    reference: e.source_id,
    structureId: e.source_type === 'structure' ? e.source_id : undefined,
  }));
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

interface ChatState {
  messages: CopilotMessage[];
  isStreaming: boolean;
  _streamInterval: ReturnType<typeof setInterval> | null;
  _conversationId: string | null;
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
      _conversationId: null,

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

        // Call the real backend copilot API
        (async () => {
          let fullText: string;
          let sources: CopilotSource[];
          let conversationId: string | null;

          try {
            const token = await getToken();
            const res = await fetch(`${API_BASE_URL}/copilot/chat`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                message: trimmed,
                conversation_id: get()._conversationId,
                context: { locale },
              }),
            });

            if (!res.ok) {
              // Token may have expired — refresh and retry once
              if (res.status === 401) {
                cachedToken = null;
                const newToken = await getToken();
                const retryRes = await fetch(`${API_BASE_URL}/copilot/chat`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${newToken}`,
                  },
                  body: JSON.stringify({
                    message: trimmed,
                    conversation_id: get()._conversationId,
                    context: { locale },
                  }),
                });
                if (!retryRes.ok) throw new Error(`Copilot API ${retryRes.status}`);
                const data: CopilotApiResponse = await retryRes.json();
                fullText = data.message;
                sources = mapEvidenceToSources(data.evidence);
                conversationId = data.conversation_id;
              } else {
                throw new Error(`Copilot API ${res.status}`);
              }
            } else {
              const data: CopilotApiResponse = await res.json();
              fullText = data.message;
              sources = mapEvidenceToSources(data.evidence);
              conversationId = data.conversation_id;
            }
          } catch (err) {
            console.error('[chat] Copilot API error:', err);
            fullText =
              locale === 'ru'
                ? 'Извините, не удалось получить ответ от сервера. Проверьте подключение к бэкенду.'
                : locale === 'kk'
                  ? 'Кешіріңіз, серверден жауап алынбады. Бэкендке қосылуын тексеріңіз.'
                  : 'Sorry, could not get a response from the server. Please check the backend connection.';
            sources = [];
            conversationId = get()._conversationId;
          }

          // Store conversation ID for continuity
          set({ _conversationId: conversationId });

          // Word-by-word streaming animation (same UX as before)
          const words = fullText.split(' ');
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
                        content: fullText,
                        sources,
                        isStreaming: false,
                      }
                    : m,
                ),
                isStreaming: false,
              }));
            }
          }, 50);

          set({ _streamInterval: streamInterval });
        })();
      },

      clearChat: () => {
        const interval = get()._streamInterval;
        if (interval) clearInterval(interval);
        set({
          messages: [],
          isStreaming: false,
          _streamInterval: null,
          _conversationId: null,
        });
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
