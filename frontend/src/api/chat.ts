import {
  apiClient,
  clearTokensAndRedirectToLogin,
  getAccessToken,
  refreshAccessTokenOrRedirect,
} from './client';

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
  type: 'start' | 'token' | 'done' | 'error' | 'tool_call' | 'thinking';
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
  const response = await sendStreamRequest(params, signal);
  await consumeEventStream(response, onEvent);
}

/**
 * POSTet den Stream-Request mit aktuellem Access-Token.
 * Bei 401 wird einmal automatisch refresht und retried — analog zum
 * Axios-Response-Interceptor in client.ts. Bei Refresh-Fehler greift
 * clearTokensAndRedirectToLogin und navigiert zu /login.
 */
async function sendStreamRequest(
  params: ChatMessageRequest,
  signal?: AbortSignal,
): Promise<Response> {
  const baseUrl = apiClient.defaults.baseURL ?? '';
  const url = `${baseUrl}/api/v1/ai/conversations/messages/stream`;
  const body = JSON.stringify(params);

  const firstResponse = await fetch(url, {
    method: 'POST',
    headers: buildStreamHeaders(getAccessToken()),
    body,
    signal,
  });

  if (firstResponse.status !== 401) {
    if (!firstResponse.ok || !firstResponse.body) {
      throw new Error(`Stream-Fehler: ${firstResponse.status}`);
    }
    return firstResponse;
  }

  // 401 → einmal refresh + retry
  const newToken = await refreshAccessTokenOrRedirect();
  const retryResponse = await fetch(url, {
    method: 'POST',
    headers: buildStreamHeaders(newToken),
    body,
    signal,
  });

  if (retryResponse.status === 401) {
    clearTokensAndRedirectToLogin();
    throw new Error('Stream-Fehler: 401 nach Token-Refresh');
  }
  if (!retryResponse.ok || !retryResponse.body) {
    throw new Error(`Stream-Fehler: ${retryResponse.status}`);
  }
  return retryResponse;
}

function buildStreamHeaders(token: string | null): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function consumeEventStream(
  response: Response,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  if (!response.body) {
    throw new Error('Stream-Fehler: kein Response-Body');
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

// --- Notifications ---

export interface ChatNotification {
  type: string;
  severity: 'info' | 'warning';
  title: string;
  message: string;
  suggested_question: string;
}

export interface NotificationsResponse {
  notifications: ChatNotification[];
  count: number;
}

export async function getChatNotifications(): Promise<NotificationsResponse> {
  const { data } = await apiClient.get<NotificationsResponse>('/api/v1/ai/notifications');
  return data;
}

// --- Plan Changes ---

export interface PlanInterval {
  type: string;
  duration_minutes?: number;
  distance_km?: number;
  target_pace_min?: string;
  target_pace_max?: string;
  target_hr_min?: number;
  target_hr_max?: number;
  repeats?: number;
  notes?: string;
}

export interface PlanRunDetails {
  run_type: string;
  target_duration_minutes?: number;
  target_pace_min?: string;
  target_pace_max?: string;
  intervals?: PlanInterval[];
}

export interface ApplyPlanChangeRequest {
  action: string;
  date: string;
  week_start?: string;
  plan_id?: number;
  description?: string;
  reason?: string;
  from?: string;
  to?: string;
  training_type?: 'running' | 'strength';
  run_details?: PlanRunDetails;
}

export interface ApplyPlanChangeResponse {
  success: boolean;
  message: string;
}

export async function applyPlanChange(
  params: ApplyPlanChangeRequest,
): Promise<ApplyPlanChangeResponse> {
  const { data } = await apiClient.post<ApplyPlanChangeResponse>(
    '/api/v1/ai/apply-plan-change',
    params,
  );
  return data;
}
