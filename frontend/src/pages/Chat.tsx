import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { Button, Card, CardBody, Breadcrumbs, BreadcrumbItem } from '@nordlig/components';
import { useChat } from '@/hooks/useChat';
import { ChatMessageBubble } from '@/components/chat/ChatMessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatQuickActions } from '@/components/chat/ChatQuickActions';
import { ConversationList } from '@/components/chat/ConversationList';
import type { ChatMessageDetail } from '@/api/chat';

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-[var(--color-bg-neutral-subtle)] text-[var(--color-text-muted)]">
        <Bot className="w-4 h-4" />
      </div>
      <div className="bg-[var(--color-bg-surface)] rounded-[var(--radius-md)] px-4 py-3">
        <div className="flex gap-1">
          <span className="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-pulse" />
          <span className="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-pulse [animation-delay:150ms]" />
          <span className="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-pulse [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onQuickAction }: { onQuickAction: (q: string) => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-6 py-12">
      <div className="w-16 h-16 rounded-full bg-[var(--color-bg-primary-subtle)] flex items-center justify-center">
        <Bot className="w-8 h-8 text-[var(--color-text-primary)]" />
      </div>
      <div className="text-center space-y-1">
        <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
          KI-Trainingsassistent
        </h2>
        <p className="text-sm text-[var(--color-text-muted)] max-w-md">
          Ich kenne deinen Trainingsplan, deine letzten Sessions und dein Wettkampfziel. Frag mich
          etwas!
        </p>
      </div>
      <ChatQuickActions onSelect={onQuickAction} />
    </div>
  );
}

interface ChatAreaProps {
  messages: ChatMessageDetail[];
  loading: boolean;
  sending: boolean;
  error: string | null;
  onSend: (text: string) => void;
  sidebarOpen: boolean;
}

function ChatArea({ messages, loading, sending, error, onSend, sidebarOpen }: ChatAreaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, sending]);

  return (
    <div className={`flex-1 flex flex-col min-w-0 ${sidebarOpen ? 'hidden lg:flex' : 'flex'}`}>
      <Card elevation="raised" className="flex-1 flex flex-col overflow-hidden">
        <CardBody className="flex-1 flex flex-col overflow-hidden p-0">
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
            {loading && (
              <div className="text-center text-sm text-[var(--color-text-muted)] py-8">
                Lade Konversation...
              </div>
            )}
            {!loading && messages.length === 0 && <EmptyState onQuickAction={onSend} />}
            {messages.map((msg) => (
              <ChatMessageBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
                timestamp={msg.created_at}
              />
            ))}
            {sending && <TypingIndicator />}
            {error && (
              <div className="text-center text-sm text-[var(--color-text-error)] py-2">{error}</div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="border-t border-[var(--color-border-base)] px-4 py-3">
            <ChatInput onSend={onSend} disabled={sending} />
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

export function ChatPage() {
  const {
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
  } = useChat();

  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  const handleSend = (text: string) => {
    void sendMessage(text);
    setSidebarOpen(false);
  };

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto">
      <header className="space-y-2 pb-2">
        <Breadcrumbs>
          <BreadcrumbItem>
            <Link to="/">Home</Link>
          </BreadcrumbItem>
          <BreadcrumbItem>KI-Chat</BreadcrumbItem>
        </Breadcrumbs>
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-[var(--color-text-base)]">
            Trainingsplan-Assistent
          </h1>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Unterhaltungen anzeigen"
            className="lg:hidden"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-5 h-5" />
            ) : (
              <PanelLeftOpen className="w-5 h-5" />
            )}
          </Button>
        </div>
      </header>

      <div className="flex gap-4" style={{ height: 'calc(100vh - 200px)' }}>
        <div
          className={`${sidebarOpen ? 'block' : 'hidden'} lg:block w-64 shrink-0 overflow-y-auto`}
        >
          <Card elevation="flat">
            <CardBody>
              <ConversationList
                conversations={conversations}
                activeId={activeConversationId}
                onSelect={(id) => {
                  void selectConversation(id);
                  setSidebarOpen(false);
                }}
                onNew={() => {
                  startNewConversation();
                  setSidebarOpen(false);
                }}
                onDelete={(id) => void removeConversation(id)}
              />
            </CardBody>
          </Card>
        </div>

        <ChatArea
          messages={messages}
          loading={loading}
          sending={sending}
          error={error}
          onSend={handleSend}
          sidebarOpen={sidebarOpen}
        />
      </div>
    </div>
  );
}
