import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User } from 'lucide-react';

function TypingDots() {
  return (
    <div className="flex gap-1 items-center h-5" aria-label="KI denkt nach...">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-[var(--color-text-muted)] motion-reduce:animate-none"
          style={{
            animation: 'typing-dot 1.4s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  );
}

interface ChatMessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export function ChatMessageBubble({ role, content, timestamp }: ChatMessageBubbleProps) {
  const isUser = role === 'user';
  const isWaiting = !isUser && content === '';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div
        className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)]'
            : 'bg-[var(--color-bg-neutral-subtle)] text-[var(--color-text-muted)]'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>
      <div
        className={`max-w-[80%] rounded-[var(--radius-md)] px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-base)]'
            : 'bg-[var(--color-bg-surface)] text-[var(--color-text-base)]'
        }`}
      >
        {isWaiting ? (
          <TypingDots />
        ) : (
          <div className="chat-markdown">
            <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
          </div>
        )}
        {timestamp && (
          <div className="mt-1.5 text-[10px] text-[var(--color-text-muted)] opacity-60">
            {new Date(timestamp).toLocaleTimeString('de-DE', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        )}
      </div>
    </div>
  );
}
