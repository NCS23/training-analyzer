import { useState, useCallback, useRef } from 'react';
import type { ChatMessageDetail, ConversationSummary, ChatMessageResponse } from '@/api/chat';
import {
  sendChatMessage,
  listConversations,
  getConversation,
  deleteConversation,
} from '@/api/chat';

interface UseChatReturn {
  messages: ChatMessageDetail[];
  conversations: ConversationSummary[];
  activeConversationId: number | null;
  sending: boolean;
  loading: boolean;
  error: string | null;
  sendMessage: (text: string) => Promise<ChatMessageResponse | null>;
  selectConversation: (id: number) => Promise<void>;
  startNewConversation: () => void;
  loadConversations: () => Promise<void>;
  removeConversation: (id: number) => Promise<void>;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessageDetail[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const idRef = useRef(0); // Lokale temp-ID fuer optimistic updates

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

  const sendMessage = useCallback(
    async (text: string): Promise<ChatMessageResponse | null> => {
      setSending(true);
      setError(null);

      // Optimistic: User-Nachricht sofort anzeigen
      idRef.current -= 1;
      const tempUserMsg: ChatMessageDetail = {
        id: idRef.current,
        role: 'user',
        content: text,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      try {
        const response = await sendChatMessage({
          message: text,
          conversation_id: activeConversationId ?? undefined,
        });

        // Neue Konversation? ID merken
        if (!activeConversationId) {
          setActiveConversationId(response.conversation_id);
        }

        // Assistent-Antwort hinzufuegen
        const assistantMsg: ChatMessageDetail = {
          id: response.message_id,
          role: 'assistant',
          content: response.content,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);

        // Konversationsliste aktualisieren
        void loadConversations();

        return response;
      } catch {
        setError('Nachricht konnte nicht gesendet werden.');
        // Optimistic Update rueckgaengig machen
        setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
        return null;
      } finally {
        setSending(false);
      }
    },
    [activeConversationId, loadConversations],
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
    sendMessage,
    selectConversation,
    startNewConversation,
    loadConversations,
    removeConversation,
  };
}
