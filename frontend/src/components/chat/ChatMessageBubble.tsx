import { Bot, User } from 'lucide-react';

interface ChatMessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

function FormatLine({ text }: { text: string }) {
  // **bold** inline formatting (safe, no innerHTML)
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith('**') && part.endsWith('**') ? (
          <strong key={i}>{part.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}

function formatContent(text: string) {
  return text.split('\n').map((line, i) => {
    if (line.startsWith('- ') || line.startsWith('• ')) {
      return (
        <li key={i} className="ml-4 list-disc">
          <FormatLine text={line.slice(2)} />
        </li>
      );
    }
    if (line.trim() === '') return <br key={i} />;
    return (
      <p key={i}>
        <FormatLine text={line} />
      </p>
    );
  });
}

export function ChatMessageBubble({ role, content, timestamp }: ChatMessageBubbleProps) {
  const isUser = role === 'user';

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
        <div className="space-y-1">{formatContent(content)}</div>
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
