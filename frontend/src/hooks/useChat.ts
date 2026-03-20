import { useState, useCallback, useRef } from 'react';
import type { ChatMessageDetail, ConversationSummary, StreamEvent } from '@/api/chat';
import {
  streamChatMessage,
  listConversations,
  getConversation,
  deleteConversation,
} from '@/api/chat';

const STREAMING_MSG_ID = -999;

function createTempMsg(id: number, role: 'user' | 'assistant', content: string): ChatMessageDetail {
  return { id, role, content, created_at: new Date().toISOString() };
}

function replaceStreamingId(msgs: ChatMessageDetail[], newId: number): ChatMessageDetail[] {
  return msgs.map((m) => (m.id === STREAMING_MSG_ID ? { ...m, id: newId } : m));
}

const TOOL_LABELS: Record<string, string> = {
  get_session_details: 'Lade Session-Details',
  search_sessions: 'Suche Sessions',
  get_training_stats: 'Berechne Statistiken',
  get_plan_details: 'Lade Trainingsplan',
  get_plan_compliance: 'Prüfe Soll/Ist',
  get_personal_records: 'Lade Bestleistungen',
  get_exercises: 'Durchsuche Übungen',
  get_ai_recommendations: 'Lade Empfehlungen',
  get_weekly_review: 'Lade Wochenrückblick',
  search_conversations: 'Durchsuche Gespräche',
  get_plan_change_log: 'Lade Planänderungen',
  propose_plan_change: 'Erstelle Planvorschlag',
  generate_training_plan: 'Generiere Trainingsplan',
  search_training_knowledge: 'Durchsuche Trainingswissen',
};

interface UseChatReturn {
  messages: ChatMessageDetail[];
  conversations: ConversationSummary[];
  activeConversationId: number | null;
  sending: boolean;
  loading: boolean;
  error: string | null;
  toolStatus: string | null;
  sendMessage: (text: string) => Promise<void>;
  cancelStream: () => void;
  selectConversation: (id: number) => Promise<void>;
  startNewConversation: () => void;
  loadConversations: () => Promise<void>;
  removeConversation: (id: number) => Promise<void>;
}

// eslint-disable-next-line max-lines-per-function -- Hook mit vielen Callbacks, Aufteilung in Sub-Hooks wuerde Lesbarkeit verschlechtern
export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessageDetail[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const idRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      const result = await listConversations();
      setConversations(result.conversations);
    } catch {
      // Stille Fehlerbehandlung — Liste bleibt leer
    }
  }, []);

  const selectConversation = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const detail = await getConversation(id);
      setMessages(detail.messages);
      setActiveConversationId(id);
    } catch {
      setError('Konversation konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, []);

  const startNewConversation = useCallback(() => {
    setActiveConversationId(null);
    setMessages([]);
    setError(null);
  }, []);

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const handleStreamEvent = useCallback(
    (event: StreamEvent) => {
      if (event.type === 'start' && event.conversation_id) {
        setActiveConversationId(event.conversation_id);
      } else if (event.type === 'token' && event.content) {
        setToolStatus(null);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === STREAMING_MSG_ID ? { ...m, content: m.content + event.content } : m,
          ),
        );
      } else if (event.type === 'tool_call' && event.name) {
        setToolStatus(TOOL_LABELS[event.name] ?? event.name);
      } else if (event.type === 'done') {
        setToolStatus(null);
        idRef.current -= 1;
        setMessages((prev) => replaceStreamingId(prev, idRef.current));
        void loadConversations();
      } else if (event.type === 'error') {
        setToolStatus(null);
        setError(event.message ?? 'Streaming-Fehler');
        setMessages((prev) => prev.filter((m) => m.id !== STREAMING_MSG_ID));
      }
    },
    [loadConversations],
  );

  const sendMessage = useCallback(
    async (text: string): Promise<void> => {
      setSending(true);
      setError(null);

      idRef.current -= 1;
      const tempUserId = idRef.current;
      setMessages((prev) => [
        ...prev,
        createTempMsg(tempUserId, 'user', text),
        createTempMsg(STREAMING_MSG_ID, 'assistant', ''),
      ]);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await streamChatMessage(
          { message: text, conversation_id: activeConversationId ?? undefined },
          handleStreamEvent,
          controller.signal,
        );
      } catch (e) {
        if (e instanceof DOMException && e.name === 'AbortError') {
          idRef.current -= 1;
          setMessages((prev) => replaceStreamingId(prev, idRef.current));
        } else {
          setError('Nachricht konnte nicht gesendet werden.');
          setMessages((prev) =>
            prev.filter((m) => m.id !== tempUserId && m.id !== STREAMING_MSG_ID),
          );
        }
      } finally {
        setSending(false);
        abortRef.current = null;
      }
    },
    [activeConversationId, handleStreamEvent],
  );

  const removeConversation = useCallback(
    async (id: number) => {
      try {
        await deleteConversation(id);
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (activeConversationId === id) {
          startNewConversation();
        }
      } catch {
        setError('Konversation konnte nicht geloescht werden.');
      }
    },
    [activeConversationId, startNewConversation],
  );

  return {
    messages,
    conversations,
    activeConversationId,
    sending,
    loading,
    error,
    toolStatus,
    sendMessage,
    cancelStream,
    selectConversation,
    startNewConversation,
    loadConversations,
    removeConversation,
  };
}
