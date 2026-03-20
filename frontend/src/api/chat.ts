import { apiClient } from './client';

// --- Types ---

export interface ChatMessageRequest {
  message: string;
  conversation_id?: number;
}

export interface ChatMessageResponse {
  conversation_id: number;
  message_id: number;
  content: string;
  provider: string;
  duration_ms: number | null;
}

export interface ChatMessageDetail {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ConversationSummary {
  id: number;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: number;
  title: string;
  messages: ChatMessageDetail[];
  created_at: string;
}

export interface ConversationListResponse {
  conversations: ConversationSummary[];
  total: number;
}

export interface StreamEvent {
  type: 'start' | 'token' | 'done' | 'error' | 'tool_call';
  conversation_id?: number;
  content?: string;
  message?: string;
  name?: string;
}

// --- API Functions ---

export async function sendChatMessage(params: ChatMessageRequest): Promise<ChatMessageResponse> {
  const { data } = await apiClient.post<ChatMessageResponse>(
    '/api/v1/ai/conversations/messages',
    params,
  );
  return data;
}

export async function streamChatMessage(
  params: ChatMessageRequest,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const baseUrl = apiClient.defaults.baseURL ?? '';
  const response = await fetch(`${baseUrl}/api/v1/ai/conversations/messages/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream-Fehler: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6)) as StreamEvent;
        onEvent(event);
      }
    }
  }
}

export async function listConversations(): Promise<ConversationListResponse> {
  const { data } = await apiClient.get<ConversationListResponse>('/api/v1/ai/conversations');
  return data;
}

export async function getConversation(id: number): Promise<ConversationDetail> {
  const { data } = await apiClient.get<ConversationDetail>(`/api/v1/ai/conversations/${id}`);
  return data;
}

export async function deleteConversation(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/ai/conversations/${id}`);
}
