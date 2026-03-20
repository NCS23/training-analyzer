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

// --- API Functions ---

export async function sendChatMessage(params: ChatMessageRequest): Promise<ChatMessageResponse> {
  const { data } = await apiClient.post<ChatMessageResponse>(
    '/api/v1/ai/conversations/messages',
    params,
  );
  return data;
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
