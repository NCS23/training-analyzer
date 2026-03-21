import { X, Pin } from 'lucide-react';
import { Button } from '@nordlig/components';

export interface ChatContext {
  type: 'session' | 'week';
  label: string;
  /** Session-ID oder Wochenstart-Datum (YYYY-MM-DD) */
  id: string;
}

interface ChatContextBadgeProps {
  context: ChatContext;
  onRemove: () => void;
}

export function ChatContextBadge({ context, onRemove }: ChatContextBadgeProps) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] text-xs">
      <Pin className="w-3 h-3 shrink-0" />
      <span className="truncate max-w-[200px]">
        {context.type === 'session' ? 'Session' : 'Woche'}: {context.label}
      </span>
      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        aria-label="Kontext entfernen"
        className="!p-0.5 !min-h-0 !min-w-0"
      >
        <X className="w-3 h-3" />
      </Button>
    </div>
  );
}
