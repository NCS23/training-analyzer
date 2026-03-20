import type { ComponentPropsWithoutRef } from 'react';
import { Link } from 'react-router-dom';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, Search, User } from 'lucide-react';
import { ChatChart } from './ChatChart';
import { parseChartBlocks } from './chartParser';
import { PlanSuggestionCard } from './PlanSuggestionCard';
import { parsePlanSuggestions } from './planSuggestionParser';
import type { PlanSuggestion } from './PlanSuggestionCard';

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

function ToolIndicator({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
      <Search
        className="w-3 h-3 motion-reduce:animate-none"
        style={{
          animation: 'typing-dot 1.4s ease-in-out infinite',
        }}
      />
      <span>{label}...</span>
    </div>
  );
}

function ChatLink({ href, children, ...props }: ComponentPropsWithoutRef<'a'>) {
  if (href?.startsWith('/')) {
    return (
      <Link to={href} className="text-[var(--color-text-primary)] underline hover:opacity-80">
        {children}
      </Link>
    );
  }
  return (
    <a href={href} {...props} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  );
}

interface ChatMessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  toolStatus?: string | null;
  onApplyPlanChange?: (suggestion: PlanSuggestion) => void;
}

export function ChatMessageBubble({
  role,
  content,
  timestamp,
  toolStatus,
  onApplyPlanChange,
}: ChatMessageBubbleProps) {
  const isUser = role === 'user';
  const isWaiting = !isUser && content === '' && !toolStatus;

  // Charts und Plan-Vorschläge aus dem Content parsen
  const { text: textWithoutCharts, charts } = !isUser
    ? parseChartBlocks(content)
    : { text: content, charts: [] };
  const { text: cleanText, suggestions } = !isUser
    ? parsePlanSuggestions(textWithoutCharts)
    : { text: textWithoutCharts, suggestions: [] };

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
        ) : toolStatus && !content ? (
          <ToolIndicator label={toolStatus} />
        ) : (
          <div className="space-y-2">
            {toolStatus && <ToolIndicator label={toolStatus} />}
            {cleanText && (
              <div className="chat-markdown">
                <Markdown remarkPlugins={[remarkGfm]} components={{ a: ChatLink }}>
                  {cleanText}
                </Markdown>
              </div>
            )}
            {charts.map((chart, i) => (
              <ChatChart key={i} chart={chart} />
            ))}
            {suggestions.map((s, i) => (
              <PlanSuggestionCard key={i} suggestion={s} onApply={onApplyPlanChange} />
            ))}
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
