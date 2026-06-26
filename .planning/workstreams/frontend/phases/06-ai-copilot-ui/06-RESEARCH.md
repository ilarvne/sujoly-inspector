# Phase 6: AI Copilot UI - Research

**Researched:** 2026-06-26
**Domain:** AI assistant chat interface, natural language Q&A, source citations, trilingual queries
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AI-01 | User can ask natural-language questions about structures ("Why is this structure marked repair required?", "Show similar incidents in this basin", "Summarize all inspections since 2022") | Mock AI engine with intent detection via keyword pattern matching against RU/KK/EN keywords. Generates structured responses with text, interactive cards, and source citations from existing mock data. |
| AI-02 | AI copilot provides evidence-grounded answers with explicit source citations (inspection records, registry rows, OSM ways, document references) displayed as clickable references | CopilotSource type with type/label/reference fields. SourceCitation component renders clickable badges under each assistant answer. Clicking a source can navigate to the related structure on the map. |
| AI-05 | AI copilot supports trilingual queries (Russian, Kazakh, English) | Mock AI engine detects query language via locale context and responds in the same language. All UI text (suggested prompts, buttons, labels) translated in all 3 message files. |
</phase_requirements>

## Summary

Phase 6 builds the AI Copilot chat interface at `/copilot`. No backend exists — all AI responses are simulated via a mock engine that pattern-matches user queries against keyword dictionaries in RU/KK/EN, queries the existing mock data layer (structures, inspections, risk scores), and generates structured responses with text, interactive cards, and source citations.

### Key Architectural Decisions

1. **Custom chat UI, no external AI chat library**: Instead of installing assistant-ui or OpenUI, build a custom chat interface using existing shadcn/ui components (Card, ScrollArea, Badge, Button, Separator, Avatar). Rationale: these libraries add dependency complexity, potential compatibility issues with Next.js 16.2.9 + Turbopack, and the mock backend means we're simulating responses anyway. A custom implementation follows existing codebase patterns exactly and gives full control over the chat UX.

2. **Mock AI engine with intent detection**: A `mockAIEngine` function takes a query string + locale, pattern-matches against trilingual keyword dictionaries to determine intent (list structures, show risk, summarize inspections, explain condition, etc.), queries the existing mock data layer, and returns a structured response (text + cards + sources). This simulates what a real LangGraph RAG agent would do.

3. **Streaming simulation**: The chat store calls the mock AI engine, gets the full response, then simulates streaming by revealing text in chunks via setTimeout. This demonstrates the SSE streaming UX that will connect to the real backend later.

4. **Interactive cards rendered inline in chat**: Custom card components (StructureCard, RiskBreakdownCard, InspectionCard, ReportCard) render structured data within assistant messages. Each card is a compact, clickable summary that can trigger navigation (e.g., clicking a StructureCard opens the passport panel on the map).

5. **Zustand chat store with persist**: Chat messages persisted to localStorage via Zustand persist middleware, so conversation history survives page refreshes. Store manages messages array, streaming state, and send/clear actions.

6. **Source citations as clickable badges**: Each assistant message can include an array of CopilotSource objects. The SourceCitationList component renders these as clickable badges. Clicking a source navigates to the related structure or opens a detail view.

## Standard Stack

### Core (Phase 6 — no new packages needed)

All functionality built with existing dependencies:
- **Zustand** (5.0.14) — chat store with persist middleware
- **TanStack Query** (5.101.1) — reuses existing structure/inspection/risk query hooks
- **shadcn/ui** — Card, Badge, Button, ScrollArea, Separator, Avatar, Progress, Tabs
- **next-intl** (4.13.0) — trilingual UI text
- **lucide-react** (1.21.0) — icons for chat UI (send, sparkles, etc.)
- **Tailwind CSS v4** — styling

### Data Flow

```
User types query → ChatStore.sendMessage()
  → Add user message to store
  → Set isStreaming = true
  → Create assistant placeholder message
  → Call mockAIEngine(query, locale)
  → Simulate streaming: reveal text chunks via setTimeout
  → Attach sources + cards to assistant message
  → Set isStreaming = false
  → Persist to localStorage
```

## Intent Detection Patterns

| Intent | Keywords (RU/KK/EN) | Response |
|--------|---------------------|----------|
| list_critical | критическ/critical/критикалық | List structures with condition=critical |
| list_repair | ремонт/repair/жөндеу | List structures with condition=repair |
| list_inspection | инспекц/inspection/тексеру | List structures needing inspection (condition=inspection) |
| show_risk | риск/risk/тәуекел | Show risk score for mentioned or top-risk structure |
| summarize_inspections | осмотр*/inspection*/тексер* | Summarize inspection history for mentioned structure |
| explain_condition | почему/why/неге + состояние/condition | Explain why a structure has its current condition |
| list_by_district | район/district/аудан | List structures in mentioned district |
| list_by_basin | бассейн/basin/алқап | List structures in mentioned basin |
| general/default | * | Fallback: summarize portfolio stats |

## Assumptions

1. No new npm packages needed — all built with existing stack
2. Mock AI engine is synchronous (computes full response, then simulates streaming)
3. Source citations reference mock data IDs (structure IDs, inspection IDs)
4. Chat history persists to localStorage but is not synced to any backend
5. The chat UI is a full-page layout (not a floating widget) at /copilot
6. Suggested prompts are trilingual and context-independent for MVP
7. Clicking a source citation navigates to the map with the structure selected

## Pitfalls

- **Streaming with setTimeout in React**: Use useRef to track timeout IDs and clear on unmount
- **Scroll to bottom on new message**: Use useRef + useEffect on messages.length
- **Zustand persist with complex objects**: Ensure messages are serializable (no functions)
- **Next.js 16 async params**: Copilot page uses `await params` pattern like other pages
- **Client component boundary**: Chat UI must be 'use client' — page stays server component that renders the client chat component
