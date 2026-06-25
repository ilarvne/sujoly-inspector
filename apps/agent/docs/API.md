# Agent API v1 Integration Guide

Base URL: `http://agent.localhost/api/v1`

## Authentication

Authentication is enabled when either `AGENT_AGENT_API_KEY` or
`AGENT_AGENT_API_KEYS` is configured.

Supported auth headers:
- `X-API-Key: <key>`
- `Authorization: Bearer <key>`

If no API key is configured, the API runs in development mode and auth is skipped.

Optional personalization headers:
- `X-Thread-ID`: Conversation thread identifier
- `X-User-ID`: User identifier for memory personalization

## Endpoints

### Models

#### List All Models
```http
GET /api/v1/models
```

**Response:**
```json
{
  "models": [
    {
      "id": "mistral-small-latest",
      "name": "Mistral Small Latest",
      "context_window": 32768,
      "max_output": 8192,
      "input_cost_per_1m": 0.1,
      "output_cost_per_1m": 0.3,
      "tier": "free"
    }
  ],
  "default_model": "mistral-small-latest"
}
```

#### Get Current Model Configuration
```http
GET /api/v1/models/current
```

**Response:**
```json
{
  "model": {
    "id": "mistral-small-latest",
    "name": "Mistral Small Latest",
    "context_window": 32768,
    "max_output": 8192,
    "input_cost_per_1m": 0.1,
    "output_cost_per_1m": 0.3,
    "tier": "free"
  },
  "temperature": 0.7,
  "max_tokens": 2048
}
```

#### Get Specific Model Info
```http
GET /api/v1/models/{model_id}
```

**Response:** `ModelInfo` object or 404

---

### Chat

#### Stream Chat (SSE)
```http
POST /api/v1/chat/stream
Content-Type: application/json
X-API-Key: your-api-key
X-Thread-ID: optional-thread-id
X-User-ID: optional-user-id
```

**Request Body:**
```json
{
  "messages": [
    {"type": "human", "content": "What is RAG?"}
  ],
  "model": "mistral-small-latest",
  "thread_id": "optional-override",
  "user_id": "optional-override"
}
```

**SSE Events:**
- `event: data` - Response chunks
- `event: end` - Stream complete
- `event: error` - Error occurred

**Example Response Stream:**
```
event: data
data: {"messages": [{"type": "ai", "content": "RAG stands for..."}]}

event: data
data: {"messages": [{"type": "ai", "content": " Retrieval-Augmented Generation..."}]}

event: end
data: {}
```

---

### Threads

#### Get Thread History
```http
GET /api/v1/threads/{thread_id}
```

**Response:**
```json
{
  "thread_id": "abc123",
  "messages": [
    {"type": "human", "content": "Hello"},
    {"type": "ai", "content": "Hi there!"}
  ]
}
```

#### Delete Thread
```http
DELETE /api/v1/threads/{thread_id}
```

**Response:**
```json
{
  "status": "deleted",
  "thread_id": "abc123"
}
```

---

### Utilities

#### Tokenize Text
```http
POST /api/v1/tokenize
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Hello, how are you?"
}
```

**Response:**
```json
{
  "tokens": 4,
  "model": "mistral-small-latest"
}
```

---

## Available Models

| Model ID | Context | Tier | Input Cost | Output Cost |
|----------|---------|------|------------|-------------|
| `mistral-small-latest` | 32K | free | $0.10/1M | $0.30/1M |
| `ministral-8b-latest` | 128K | free | $0.10/1M | $0.10/1M |
| `ministral-3b-latest` | 128K | free | $0.04/1M | $0.04/1M |
| `open-mixtral-8x7b` | 32K | free | $0.70/1M | $0.70/1M |
| `open-mixtral-8x22b` | 65K | paid | $2.00/1M | $6.00/1M |
| `mistral-medium-latest` | 32K | paid | $2.70/1M | $8.10/1M |
| `mistral-large-latest` | 128K | paid | $2.00/1M | $6.00/1M |
| `codestral-latest` | 32K | paid | $0.30/1M | $0.90/1M |

---

## TypeScript Integration Example

```typescript
interface ChatMessage {
  type: 'human' | 'assistant';
  content: string;
}

interface ChatRequest {
  messages: ChatMessage[];
  model?: string;
  thread_id?: string;
  user_id?: string;
}

async function streamChat(request: ChatRequest, threadId?: string): Promise<void> {
  const response = await fetch('http://agent.localhost/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(threadId && { 'X-Thread-ID': threadId }),
    },
    body: JSON.stringify(request),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        const event = line.slice(7);
        if (event === 'end') return;
        if (event === 'error') throw new Error('Stream error');
      }
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        console.log('Received:', data);
      }
    }
  }
}

// Usage
await streamChat({
  messages: [{ type: 'human', content: 'Hello!' }],
  model: 'mistral-small-latest'
}, 'my-thread-id');
```

---

## React Hook Example

```typescript
import { useState, useCallback } from 'react';

interface UseAgentChatOptions {
  threadId?: string;
  userId?: string;
  model?: string;
}

export function useAgentChat(options: UseAgentChatOptions = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    const userMessage: ChatMessage = { type: 'human', content };
    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);
    setError(null);

    try {
      const response = await fetch('http://agent.localhost/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(options.threadId && { 'X-Thread-ID': options.threadId }),
          ...(options.userId && { 'X-User-ID': options.userId }),
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          model: options.model,
        }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        for (const line of chunk.split('\n')) {
          if (line.startsWith('data: ') && !line.includes('event:')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.messages?.[0]?.content) {
                assistantContent += data.messages[0].content;
                setMessages(prev => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (updated[lastIdx]?.type === 'assistant') {
                    updated[lastIdx] = { type: 'assistant', content: assistantContent };
                  } else {
                    updated.push({ type: 'assistant', content: assistantContent });
                  }
                  return updated;
                });
              }
            } catch {}
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsStreaming(false);
    }
  }, [messages, options]);

  return { messages, sendMessage, isStreaming, error };
}
```

---

## Health & Metrics

```http
GET /health          # Basic health check
GET /health/live     # Kubernetes liveness probe
GET /metrics         # JSON metrics
GET /metrics/prom    # Prometheus format
```

---

## Rate Limiting

Default: 20 requests/minute per user (configurable via `AGENT_RATE_LIMIT_PER_USER`)

Rate limit headers returned:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:
- `400` - Bad request (invalid input)
- `404` - Resource not found
- `429` - Rate limit exceeded
- `500` - Internal server error
