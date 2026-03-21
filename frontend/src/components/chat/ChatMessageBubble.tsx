import type { ComponentPropsWithoutRef } from 'react';
import { Link } from 'react-router-dom';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, Search, User } from 'lucide-react';
import type { ChartData } from './ChatChart';
import { ChatChart } from './ChatChart';
import { parseChartBlocks } from './chartParser';
import type { PlanCreatedInfo } from './PlanCreatedCard';
import { PlanCreatedCard } from './PlanCreatedCard';
import { parsePlanCreated } from './planCreatedParser';
import type { PlanSuggestion } from './PlanSuggestionCard';
import { PlanSuggestionCard } from './PlanSuggestionCard';
import { parsePlanSuggestions } from './planSuggestionParser';

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

interface ParsedContent {
  text: string;
  charts: ChartData[];
  plans: PlanCreatedInfo[];
  suggestions: PlanSuggestion[];
}

/** Parst Charts, Plan-Erstellungen und Plan-Vorschläge aus dem Content. */
function parseAssistantContent(content: string): ParsedContent {
  const { text: t1, charts } = parseChartBlocks(content);
  const { text: t2, plans } = parsePlanCreated(t1);
  const { text, suggestions } = parsePlanSuggestions(t2);
  return { text, charts, plans, suggestions };
}

interface ChatMessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  toolStatus?: string | null;
}

export function ChatMessageBubble({
  role,
  content,
  timestamp,
  toolStatus,
}: ChatMessageBubbleProps) {
  const isUser = role === 'user';
  const isWaiting = !isUser && content === '' && !toolStatus;

  const parsed = !isUser
    ? parseAssistantContent(content)
    : { text: content, charts: [], plans: [], suggestions: [] };

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
          <BubbleContent toolStatus={toolStatus} parsed={parsed} />
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

function BubbleContent({
  toolStatus,
  parsed,
}: {
  toolStatus?: string | null;
  parsed: ParsedContent;
}) {
  return (
    <div className="space-y-2">
      {parsed.text && (
        <div className="chat-markdown">
          <Markdown remarkPlugins={[remarkGfm]} components={{ a: ChatLink }}>
            {parsed.text}
          </Markdown>
        </div>
      )}
      {parsed.plans.map((p, i) => (
        <PlanCreatedCard key={i} plan={p} />
      ))}
      {parsed.charts.map((chart, i) => (
        <ChatChart key={i} chart={chart} />
      ))}
      {parsed.suggestions.map((s, i) => (
        <PlanSuggestionCard key={i} suggestion={s} />
      ))}
      {toolStatus && <ToolIndicator label={toolStatus} />}
    </div>
  );
}
