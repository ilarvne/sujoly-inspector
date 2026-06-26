'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CopilotMessage, CopilotSource, CopilotSourceType } from '@/lib/api/types';

type Locale = 'ru' | 'kk' | 'en';

// ---------------------------------------------------------------------------
// Backend configuration & auth (mirrors lib/api/client.ts)
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';
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

        // Call the agent SSE endpoint (LangGraph agentic RAG with alemllm)
        (async () => {
          let fullText: string;
          let sources: CopilotSource[];
          let conversationId: string | null;

          try {
            const token = await getToken();
            const res = await fetch(`${API_BASE_URL}/chat/stream`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                messages: [{ type: 'human', content: trimmed }],
              }),
            });

            if (!res.ok) throw new Error(`Agent API ${res.status}`);

            // Parse SSE stream and accumulate text
            const reader = res.body?.getReader();
            if (!reader) throw new Error('No response body');

            const decoder = new TextDecoder();
            let buffer = '';
            let accumulated = '';

            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (line.startsWith('event: messages')) {
                  // Next data line has the content
                } else if (line.startsWith('data: ') && accumulated !== '__WAITING__') {
                  try {
                    const payload = JSON.parse(line.slice(6));
                    if (payload.content) {
                      accumulated += payload.content;
                      set((state) => ({
                        messages: state.messages.map((m) =>
                          m.id === assistantId
                            ? { ...m, content: accumulated }
                            : m,
                        ),
                      }));
                    }
                  } catch {
                    // skip non-JSON data lines
                  }
                }
              }
            }

            fullText = accumulated || (locale === 'ru' ? 'Нет ответа от агента.' : 'No response from agent.');
            sources = [];
            conversationId = get()._conversationId;
          } catch (err) {
            console.error('[chat] Agent API error:', err);
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

          // Finalize the message
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
