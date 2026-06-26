import { describe, it, expect, beforeEach } from 'vitest';
import { detectIntent, mockAIEngine, getSuggestedPrompts } from '@/lib/copilot/mock-ai-engine';
import { useChatStore } from '@/lib/stores/chat-store';

describe('Phase 6 mock AI engine', () => {
  describe('detectIntent', () => {
    it('detects list_critical intent from RU keywords', () => {
      expect(detectIntent('какие сооружения в критическом состоянии?')).toBe('list_critical');
    });

    it('detects list_critical intent from EN keywords', () => {
      expect(detectIntent('Which structures are in critical condition?')).toBe('list_critical');
    });

    it('detects list_critical intent from KK keywords', () => {
      expect(detectIntent('Қандай құрылымдар критикалық жағдайда?')).toBe('list_critical');
    });

    it('detects list_repair intent', () => {
      expect(detectIntent('Покажи сооружения требующие ремонта')).toBe('list_repair');
      expect(detectIntent('Show structures requiring repair')).toBe('list_repair');
    });

    it('detects list_inspection intent', () => {
      expect(detectIntent('Какие сооружения нуждаются в инспекции?')).toBe('list_inspection');
      expect(detectIntent('Which structures need inspection?')).toBe('list_inspection');
    });

    it('detects show_risk intent', () => {
      expect(detectIntent('Покажи уровень риска')).toBe('show_risk');
      expect(detectIntent('Show risk level')).toBe('show_risk');
    });

    it('detects summarize_inspections intent', () => {
      expect(detectIntent('Summarize all inspections since 2022')).toBe('summarize_inspections');
      expect(detectIntent('История осмотров сооружения')).toBe('summarize_inspections');
    });

    it('detects explain_condition intent', () => {
      expect(detectIntent('Почему это сооружение в таком состоянии?')).toBe('explain_condition');
      expect(detectIntent('Why is this structure marked repair required?')).toBe('explain_condition');
    });

    it('detects list_by_district intent', () => {
      expect(detectIntent('Сооружения по районам')).toBe('list_by_district');
      expect(detectIntent('Structures by district')).toBe('list_by_district');
    });

    it('detects list_by_basin intent', () => {
      expect(detectIntent('Сооружения по бассейнам')).toBe('list_by_basin');
      expect(detectIntent('Structures by basin')).toBe('list_by_basin');
    });

    it('returns general for unrecognized queries', () => {
      expect(detectIntent('Hello world')).toBe('general');
      expect(detectIntent('')).toBe('general');
    });
  });

  describe('mockAIEngine', () => {
    it('returns text, sources, and cards for list_critical intent', () => {
      const result = mockAIEngine('Which structures are critical?', 'en');
      expect(result.text).toBeTruthy();
      expect(result.text.length).toBeGreaterThan(0);
      expect(result.sources.length).toBeGreaterThan(0);
      expect(result.cards.length).toBeGreaterThan(0);
      expect(result.cards[0].type).toBe('structure');
    });

    it('returns risk cards for show_risk intent', () => {
      const result = mockAIEngine('Show top risk structures', 'en');
      expect(result.text).toBeTruthy();
      expect(result.cards.length).toBeGreaterThan(0);
      expect(result.cards[0].type).toBe('risk');
    });

    it('returns inspection cards for summarize_inspections intent', () => {
      const result = mockAIEngine('Summarize inspections', 'en');
      expect(result.text).toBeTruthy();
      expect(result.cards.some((c) => c.type === 'inspection')).toBe(true);
    });

    it('returns report card for general intent', () => {
      const result = mockAIEngine('Hello', 'en');
      expect(result.text).toContain('55');
      expect(result.cards.some((c) => c.type === 'report')).toBe(true);
    });

    it('responds in Russian when locale is ru', () => {
      const result = mockAIEngine('Какие сооружения критические?', 'ru');
      expect(result.text).toContain('критическ');
    });

    it('responds in Kazakh when locale is kk', () => {
      const result = mockAIEngine('Қандай құрылымдар критикалық?', 'kk');
      expect(result.text).toContain('критикалық');
    });

    it('responds in English when locale is en', () => {
      const result = mockAIEngine('Which structures are critical?', 'en');
      expect(result.text).toContain('critical');
    });

    it('sources have required fields', () => {
      const result = mockAIEngine('Show critical structures', 'en');
      for (const source of result.sources) {
        expect(source.id).toBeDefined();
        expect(source.type).toBeDefined();
        expect(source.label).toBeDefined();
        expect(source.reference).toBeDefined();
      }
    });
  });

  describe('getSuggestedPrompts', () => {
    it('returns 5 prompts for English', () => {
      const prompts = getSuggestedPrompts('en');
      expect(prompts.length).toBe(5);
      expect(prompts[0]).toContain('critical');
    });

    it('returns 5 prompts for Russian', () => {
      const prompts = getSuggestedPrompts('ru');
      expect(prompts.length).toBe(5);
      expect(prompts[0]).toContain('критическ');
    });

    it('returns 5 prompts for Kazakh', () => {
      const prompts = getSuggestedPrompts('kk');
      expect(prompts.length).toBe(5);
      expect(prompts[0]).toContain('критикалық');
    });
  });
});

describe('Phase 6 chat store', () => {
  beforeEach(() => {
    useChatStore.getState().clearChat();
  });

  it('starts with empty messages', () => {
    expect(useChatStore.getState().messages).toEqual([]);
    expect(useChatStore.getState().isStreaming).toBe(false);
  });

  it('clearChat empties messages', () => {
    useChatStore.setState({ messages: [{ id: 'test', role: 'user', content: 'test', timestamp: new Date().toISOString() }] });
    useChatStore.getState().clearChat();
    expect(useChatStore.getState().messages).toEqual([]);
  });

  it('sendMessage adds user and assistant messages', () => {
    useChatStore.getState().sendMessage('Test query', 'en');
    const messages = useChatStore.getState().messages;
    expect(messages.length).toBe(2);
    expect(messages[0].role).toBe('user');
    expect(messages[0].content).toBe('Test query');
    expect(messages[1].role).toBe('assistant');
    expect(messages[1].isStreaming).toBe(true);
  });

  it('sets isStreaming to true during send', () => {
    useChatStore.getState().sendMessage('Test query', 'en');
    expect(useChatStore.getState().isStreaming).toBe(true);
  });

  it('does not send empty messages', () => {
    useChatStore.getState().sendMessage('   ', 'en');
    expect(useChatStore.getState().messages.length).toBe(0);
  });
});
